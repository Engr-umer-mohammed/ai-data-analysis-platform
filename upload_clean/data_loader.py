# data_loader.py
# Universal Data Loader — AI Data Analysis Agent
# Version 2.1 — Developer reviewed and corrected
#
# CHANGES FROM v2.0:
#   Fixed mixed indentation errors in _clean_dataframe
#   Added Excel date misinterpretation correction (Step 6)
#   Fixes math scores showing as 1/1/1970 12:00:00 AM
#   Removed deprecated infer_datetime_format parameter
#   from pd.to_datetime calls (removed in pandas 2.0+)
#   Added per-step try/except in whitespace stripping
#   Added explicit step comments throughout cleaning
#   Expanded numeric column indicator keyword list
#   All indentation normalized to 4 spaces throughout

import os
import json
import logging
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


# ════════════════════════════════════════════════════════
# DATASET PROFILE
# ════════════════════════════════════════════════════════

@dataclass
class DatasetProfile:
    """
    The standardized contract between the data loader
    and every downstream component in the pipeline.

    Every field is populated by the loader before
    the profile is handed to the statistical analyzer,
    visualizer, or report generator. Downstream
    components never read the raw file — they work
    exclusively with this object and the dataframe
    it carries.

    The separation between numeric_columns,
    text_columns, and datetime_columns is critical.
    The statistical analyzer operates only on
    numeric_columns. If a datetime column appears
    there, float() coercion failures result. The
    loader is responsible for ensuring these lists
    are mutually exclusive and correctly classified
    before the profile leaves this module.
    """

    dataframe:        pd.DataFrame   = None

    file_name:        str            = ""
    file_format:      str            = ""
    file_size_kb:     float          = 0.0

    total_rows:       int            = 0
    total_columns:    int            = 0
    column_names:     list           = field(default_factory=list)
    numeric_columns:  list           = field(default_factory=list)
    text_columns:     list           = field(default_factory=list)
    datetime_columns: list           = field(default_factory=list)

    total_missing_values: int        = 0
    missing_by_column:    dict       = field(default_factory=dict)
    duplicate_rows:       int        = 0
    completeness_percent: float      = 100.0

    has_time_series:  bool           = False
    time_column:      Optional[str]  = None
    time_range_start: Optional[str]  = None
    time_range_end:   Optional[str]  = None

    loaded_at:        str            = ""
    load_success:     bool           = False
    load_error:       Optional[str]  = None
    warnings:         list           = field(default_factory=list)


# ════════════════════════════════════════════════════════
# UNIVERSAL DATA LOADER
# ════════════════════════════════════════════════════════

class UniversalDataLoader:
    """
    Reads any supported file format, cleans the raw
    data without destroying information, classifies
    every column by its true data type, detects
    temporal structure automatically, and delivers
    a fully validated DatasetProfile ready for the
    analysis pipeline.

    The loader is intentionally unopinionated about
    domain. It does not know or care whether the data
    describes power system faults, hospital patients,
    retail transactions, or student examination scores.
    Its responsibility is structural understanding
    and type safety — nothing more.

    Supported formats:
        CSV  — comma, semicolon, tab, pipe delimited
        Excel — .xlsx and .xls, first sheet loaded
        JSON  — array of objects, object of arrays,
                nested with data/records/rows key
        TXT  — delimited or number-per-line plain text
    """

    MAX_ROWS_DEFAULT              = 100_000
    CATEGORICAL_UNIQUE_THRESHOLD  = 0.05
    DATETIME_VALID_RATIO_REQUIRED = 0.80

    # Keywords that identify columns that should be
    # numeric even if the file parser misread them
    # as dates. Used in Excel date correction step.
    NUMERIC_COLUMN_INDICATORS = [
        "score", "grade", "mark", "result", "gpa",
        "rate", "count", "amount", "total", "sum",
        "number", "qty", "quantity", "age",
        "salary", "revenue", "cost", "price", "fee",
        "weight", "height", "distance", "speed",
        "percent", "pct", "ratio", "index", "rank",
        "points", "goals", "assists", "rating",
        "temperature", "pressure", "voltage", "current",
        "frequency", "duration", "size", "length",
        "width", "depth", "area", "volume", "value",
        "balance", "profit", "loss", "income", "tax",
        "attendance", "absent", "present", "pass",
        "fail", "correct", "wrong", "attempt",
    ]

    def __init__(self, max_rows: int = None):
        self.max_rows = max_rows or self.MAX_ROWS_DEFAULT

    # ════════════════════════════════════════════════════
    # PRIMARY ENTRY POINT
    # ════════════════════════════════════════════════════

    def load(self, file_path: str) -> DatasetProfile:
        """
        Accept any supported file path and return a
        fully populated DatasetProfile regardless of
        outcome. On failure, load_success is False
        and load_error contains the diagnostic message.
        The caller never receives an exception from
        this method — all failures are encapsulated
        inside the profile object.
        """

        profile           = DatasetProfile()
        profile.loaded_at = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        if not os.path.exists(file_path):
            profile.load_error = (
                f"File not found at path: {file_path}\n"
                f"Verify the path is correct and the "
                f"file has not been moved or deleted."
            )
            logger.error(profile.load_error)
            return profile

        profile.file_name    = os.path.basename(file_path)
        profile.file_size_kb = round(
            os.path.getsize(file_path) / 1024, 2
        )

        extension           = (
            os.path.splitext(file_path)[1].lower()
        )
        profile.file_format = extension

        logger.info(
            f"Loading: {profile.file_name} "
            f"({profile.file_size_kb} KB | {extension})"
        )

        try:
            if extension == ".csv":
                df = self._read_csv(file_path, profile)
            elif extension in [".xlsx", ".xls"]:
                df = self._read_excel(file_path, profile)
            elif extension == ".json":
                df = self._read_json(file_path, profile)
            elif extension == ".txt":
                df = self._read_txt(file_path, profile)
            else:
                profile.load_error = (
                    f"Unsupported file format: {extension}\n"
                    f"Supported formats: "
                    f".csv  .xlsx  .xls  .json  .txt"
                )
                return profile

            if df is None or df.empty:
                profile.load_error = (
                    "The file was read successfully but "
                    "contains no data. Verify the file "
                    "is not empty and has at least one "
                    "row of values below a header row."
                )
                return profile

            # Run pipeline in correct order
            df = self._clean_dataframe(df, profile)
            self._profile_dataframe(df, profile)
            self._detect_time_series(df, profile)
            self._validate_column_classifications(profile)

            profile.dataframe    = df
            profile.load_success = True

            logger.info(
                f"Load complete: "
                f"{profile.total_rows:,} rows | "
                f"{profile.total_columns} columns | "
                f"{len(profile.numeric_columns)} numeric | "
                f"{len(profile.datetime_columns)} datetime | "
                f"time_series={profile.has_time_series}"
            )

        except Exception as error:
            profile.load_error = (
                f"Unexpected failure during load: "
                f"{str(error)}"
            )
            logger.error(
                f"Load failed for {file_path}: {error}",
                exc_info=True
            )

        return profile

    # ════════════════════════════════════════════════════
    # FORMAT READERS
    # ════════════════════════════════════════════════════

    def _read_csv(
        self,
        file_path: str,
        profile:   DatasetProfile
    ) -> Optional[pd.DataFrame]:
        """
        Read CSV files with automatic delimiter detection
        across comma, semicolon, tab, and pipe separators.
        Encoding is attempted in order of global prevalence
        before falling back to pandas engine-level detection.
        Malformed rows are skipped with a warning rather
        than raising an exception that stops the entire load.
        """

        delimiters = [",", ";", "\t", "|"]
        encodings  = [
            "utf-8", "utf-8-sig", "latin-1", "cp1252"
        ]

        for encoding in encodings:
            for delimiter in delimiters:
                try:
                    df = pd.read_csv(
                        file_path,
                        delimiter    = delimiter,
                        encoding     = encoding,
                        nrows        = self.max_rows,
                        on_bad_lines = "skip"
                    )

                    if df.shape[1] > 1:
                        logger.info(
                            f"CSV parsed: "
                            f"delimiter='{delimiter}' "
                            f"encoding='{encoding}'"
                        )
                        if encoding != "utf-8":
                            profile.warnings.append(
                                f"Non-standard encoding "
                                f"used: {encoding}. "
                                f"If special characters "
                                f"appear corrupted, "
                                f"re-save the file as "
                                f"UTF-8 before reloading."
                            )
                        return df

                except Exception:
                    continue

        try:
            df = pd.read_csv(
                file_path,
                sep          = None,
                engine       = "python",
                nrows        = self.max_rows,
                on_bad_lines = "skip"
            )
            profile.warnings.append(
                "Delimiter could not be detected from "
                "standard options. Automatic engine "
                "detection was used. Verify column "
                "structure in the output."
            )
            return df

        except Exception as error:
            raise ValueError(
                f"CSV could not be read with any "
                f"delimiter or encoding "
                f"combination: {error}"
            )

    def _read_excel(
        self,
        file_path: str,
        profile:   DatasetProfile
    ) -> Optional[pd.DataFrame]:
        """
        Read Excel files, loading the first sheet by
        default. When multiple sheets are present,
        their names are recorded as a warning so the
        analyst is aware that additional data exists
        beyond what was loaded. Merged cells and
        trailing empty rows are handled gracefully
        by pandas without explicit preprocessing.
        """

        try:
            xl         = pd.ExcelFile(file_path)
            all_sheets = xl.sheet_names

            if len(all_sheets) > 1:
                profile.warnings.append(
                    f"Excel workbook contains "
                    f"{len(all_sheets)} sheets: "
                    f"{all_sheets}. Only the first "
                    f"sheet '{all_sheets[0]}' was "
                    f"loaded. To analyze other sheets, "
                    f"export them individually as "
                    f"separate CSV files."
                )

            df = pd.read_excel(
                file_path,
                sheet_name = all_sheets[0],
                nrows      = self.max_rows
            )

            logger.info(
                f"Excel loaded: "
                f"sheet='{all_sheets[0]}'"
            )
            return df

        except ImportError:
            raise ValueError(
                "openpyxl is required to read "
                "Excel files.\n"
                "Install it with: pip install openpyxl"
            )
        except Exception as error:
            raise ValueError(
                f"Excel file could not be read: {error}"
            )

    def _read_json(
        self,
        file_path: str,
        profile:   DatasetProfile
    ) -> Optional[pd.DataFrame]:
        """
        Read JSON files across three common structural
        patterns encountered in real-world API exports,
        database dumps, and manually constructed datasets.
        Nested structures are automatically flattened
        using pandas json_normalize rather than requiring
        the user to pre-process their JSON before analysis.
        """

        try:
            with open(
                file_path, "r", encoding="utf-8"
            ) as f:
                raw = json.load(f)
        except json.JSONDecodeError as error:
            raise ValueError(
                f"JSON file contains invalid "
                f"syntax: {error}\n"
                f"Validate the file at "
                f"jsonlint.com before retrying."
            )

        if isinstance(raw, list):
            df = pd.json_normalize(raw)
            logger.info(
                "JSON loaded: array of objects structure."
            )
            return df

        if isinstance(raw, dict):
            values = list(raw.values())

            if values and isinstance(values[0], list):
                df = pd.DataFrame(raw)
                logger.info(
                    "JSON loaded: "
                    "object-with-array-values structure."
                )
                return df

            for key in [
                "data", "records", "rows",
                "items", "results"
            ]:
                if (
                    key in raw and
                    isinstance(raw[key], list)
                ):
                    df = pd.json_normalize(raw[key])
                    profile.warnings.append(
                        f"Data extracted from nested "
                        f"JSON key: '{key}'. "
                        f"Top-level metadata ignored."
                    )
                    logger.info(
                        f"JSON loaded: nested "
                        f"under key '{key}'."
                    )
                    return df

            df = pd.json_normalize([raw])
            profile.warnings.append(
                "JSON contained a single object "
                "rather than an array. Loaded as a "
                "one-row dataset. If this is "
                "unexpected, verify the file structure."
            )
            return df

        raise ValueError(
            "JSON structure was not recognized. "
            "The file must contain an array of objects "
            "or an object with array values to be "
            "loaded as tabular data."
        )

    def _read_txt(
        self,
        file_path: str,
        profile:   DatasetProfile
    ) -> Optional[pd.DataFrame]:
        """
        Read plain text files by attempting delimiter-based
        parsing first across the five most common separators.
        When no consistent delimiter is found, numeric values
        are extracted line by line and assembled into a
        dataframe with auto-generated column names. This
        fallback handles custom export formats from legacy
        instrumentation and measurement systems that produce
        columnar numeric output without formal headers.
        """

        delimiters = [",", "\t", "|", ";", " "]

        for delimiter in delimiters:
            try:
                df = pd.read_csv(
                    file_path,
                    delimiter    = delimiter,
                    nrows        = self.max_rows,
                    on_bad_lines = "skip"
                )
                if df.shape[1] > 1:
                    logger.info(
                        f"TXT parsed as delimited: "
                        f"delimiter='{delimiter}'"
                    )
                    profile.warnings.append(
                        f"TXT file treated as delimited "
                        f"text using '{delimiter}' as "
                        f"separator. Verify columns are "
                        f"correctly separated."
                    )
                    return df
            except Exception:
                continue

        try:
            import re
            rows = []

            with open(
                file_path, "r", encoding="utf-8"
            ) as f:
                lines = f.readlines()

            for line in lines:
                line    = line.strip()
                if not line or line.startswith("#"):
                    continue
                numbers = re.findall(
                    r"[-+]?\d*\.?\d+", line
                )
                if numbers:
                    rows.append(
                        [float(n) for n in numbers]
                    )

            if rows:
                max_cols = max(len(r) for r in rows)
                padded   = [
                    r + [None] * (max_cols - len(r))
                    for r in rows
                ]
                cols = [
                    f"column_{i + 1}"
                    for i in range(max_cols)
                ]
                df = pd.DataFrame(padded, columns=cols)
                profile.warnings.append(
                    "TXT file had no consistent delimiter. "
                    "Numeric values were extracted per line "
                    "and auto-assigned column names. Review "
                    "the column structure before interpreting "
                    "results."
                )
                logger.info(
                    "TXT loaded via numeric extraction fallback."
                )
                return df

        except Exception as error:
            raise ValueError(
                f"TXT file could not be read "
                f"in any format: {error}"
            )

        raise ValueError(
            "TXT file parsing exhausted all strategies. "
            "Ensure the file contains either delimited "
            "columns or one or more numeric values per line."
        )

    # ════════════════════════════════════════════════════
    # DATA CLEANING — v2.1 Complete Fixed Version
    # ════════════════════════════════════════════════════

    def _clean_dataframe(
        self,
        df:      pd.DataFrame,
        profile: DatasetProfile
    ) -> pd.DataFrame:
        """
        Apply a principled sequence of cleaning operations
        to the raw dataframe. Every operation is logged
        when it changes the data so the analyst has a
        complete audit trail of what was modified and why.

        The cleaning philosophy is conservative — operations
        that remove or modify data are only applied when
        the evidence is unambiguous. Only genuinely
        uninformative content is eliminated.

        Cleaning sequence:
            Step 1 — Standardize column names
            Step 2 — Drop unnamed Excel artifact columns
            Step 3 — Remove completely empty rows
            Step 4 — Remove completely empty columns
            Step 5 — Remove exact duplicate rows
            Step 6 — Fix Excel date misinterpretation
            Step 7 — Convert numeric text columns
            Step 8 — Strip whitespace from text columns
        """

        original_rows = len(df)
        original_cols = len(df.columns)

        # ── STEP 1 — Standardize column names ───────────
        df.columns = (
            df.columns
            .str.strip()
            .str.lower()
            .str.replace(r"[^\w\s]", "", regex=True)
            .str.replace(r"\s+", "_", regex=True)
            .str.replace(r"_+", "_", regex=True)
        )

        # ── STEP 2 — Drop unnamed Excel artifact columns ─
        unnamed_mask = df.columns.str.startswith("unnamed")
        if unnamed_mask.any():
            df = df.loc[:, ~unnamed_mask]
            profile.warnings.append(
                "Removed unnamed columns produced by Excel export."
            )

        # ── STEP 3 — Remove completely empty rows ──────
        df = df.dropna(how="all")

        # ── STEP 4 — Remove completely empty columns ──
        df = df.dropna(axis=1, how="all")

        # ── STEP 5 — Remove exact duplicate rows ──────
        dupes = df.duplicated().sum()
        if dupes > 0:
            df = df.drop_duplicates()
            profile.duplicate_rows = int(dupes)
            profile.warnings.append(
                f"{dupes} exact duplicate row"
                f"{'s were' if dupes > 1 else ' was'} "
                f"removed during cleaning."
            )

        # ── STEP 6 — Fix Excel date misinterpretation ──
        for col in df.columns:
            # Check if column name contains numeric indicators
            is_numeric_indicator = any(
                indicator in col.lower()
                for indicator in self.NUMERIC_COLUMN_INDICATORS
            )
            # If pandas already converted to datetime but column name suggests numeric
            if is_numeric_indicator and pd.api.types.is_datetime64_any_dtype(df[col]):
                try:
                    # Convert datetime to numeric (days since epoch)
                    df[col] = (df[col] - pd.Timestamp("1970-01-01")).dt.days
                    # Then convert to numeric if it looks like a score
                    if df[col].mean() > 0:
                        df[col] = pd.to_numeric(df[col], errors="coerce")
                        profile.warnings.append(
                            f"Column '{col}' was misinterpreted as a date. "
                            f"Converted back to numeric values."
                        )
                except Exception as e:
                    logger.debug(f"Could not fix date misinterpretation for '{col}': {e}")

        # ── STEP 7 — Convert text columns that are actually numeric ──
        for col in df.columns:
            if df[col].dtype == object:
                converted = pd.to_numeric(df[col], errors="coerce")
                non_null_original = df[col].notna().sum()
                non_null_converted = converted.notna().sum()
                if (
                    non_null_original > 0 and
                    non_null_converted / non_null_original >= 0.85
                ):
                    df[col] = converted
                    profile.warnings.append(
                        f"Column '{col}' was stored as text but "
                        f"contains numeric values. It has been "
                        f"converted to numeric type for analysis."
                    )

        # ── STEP 8 — Strip whitespace from text columns ──
        for col in df.select_dtypes(include="object").columns:
            try:
                df[col] = df[col].str.strip()
            except Exception:
                continue

        removed_rows = original_rows - len(df)
        removed_cols = original_cols - len(df.columns)

        if removed_rows > 0:
            profile.warnings.append(
                f"{removed_rows} empty or duplicate row"
                f"{'s were' if removed_rows > 1 else ' was'} "
                f"removed during cleaning."
            )
        if removed_cols > 0:
            profile.warnings.append(
                f"{removed_cols} empty or unnamed column"
                f"{'s were' if removed_cols > 1 else ' was'} "
                f"removed during cleaning."
            )

        logger.info(
            f"Cleaning complete: {len(df)} rows | "
            f"{len(df.columns)} columns remaining"
        )
        return df

    # ════════════════════════════════════════════════════
    # DATASET PROFILING
    # ════════════════════════════════════════════════════

    def _profile_dataframe(
        self,
        df:      pd.DataFrame,
        profile: DatasetProfile
    ) -> None:
        """
        Populate the structural fields of the profile
        based on the cleaned dataframe. Column type
        classification at this stage is based on pandas
        dtype inference alone. The time series detection
        step that follows may reclassify columns after
        attempting datetime parsing — which is why
        _validate_column_classifications runs last
        to enforce mutual exclusivity.
        """

        profile.total_rows    = len(df)
        profile.total_columns = len(df.columns)
        profile.column_names  = df.columns.tolist()

        profile.numeric_columns  = (
            df.select_dtypes(include=[np.number])
            .columns.tolist()
        )
        profile.text_columns     = (
            df.select_dtypes(include=["object"])
            .columns.tolist()
        )
        profile.datetime_columns = (
            df.select_dtypes(include=["datetime64"])
            .columns.tolist()
        )

        missing_counts                = df.isnull().sum()
        profile.total_missing_values  = int(missing_counts.sum())
        profile.missing_by_column     = {
            col: int(count)
            for col, count in missing_counts.items()
            if count > 0
        }

        total_cells = profile.total_rows * profile.total_columns
        if total_cells > 0:
            profile.completeness_percent = round(
                (
                    (total_cells - profile.total_missing_values)
                    / total_cells
                ) * 100,
                2
            )

        logger.info(
            f"Profiling complete: "
            f"{len(profile.numeric_columns)} numeric | "
            f"{len(profile.text_columns)} text | "
            f"{len(profile.datetime_columns)} datetime | "
            f"{profile.completeness_percent}% complete"
        )

    # ════════════════════════════════════════════════════
    # TIME SERIES DETECTION
    # ════════════════════════════════════════════════════

    def _detect_time_series(
        self,
        df:      pd.DataFrame,
        profile: DatasetProfile
    ) -> None:
        """
        Detect whether the dataset contains a time
        dimension by scanning column names and attempting
        datetime parsing on any column that either has
        a time-related name or is currently classified
        as a text column.

        CRITICAL FIX (v2.0):
        When a column is confirmed as datetime, it is
        immediately removed from numeric_columns and text_columns
        and added to datetime_columns to prevent float()
        coercion errors in the statistical analyzer.

        v2.1: Added exclusion list to prevent subject/score
        columns from being converted to datetime.
        """

        # ─── EXCLUSION LIST ──────────────────────────────────────────
        # These column names should NEVER be treated as dates
        EXCLUDE_COLUMNS = [
            # Subjects
            'math', 'maths', 'mathematics', 'science', 'physics',
            'chemistry', 'biology', 'english', 'history', 'geography',
            'art', 'music', 'pe', 'physical_education',
            # Scores and grades
            'score', 'grade', 'mark', 'gpa', 'avg', 'average',
            'total', 'sum', 'count', 'rank', 'percent', 'percentage',
            # Student data
            'student', 'name', 'first_name', 'last_name', 'id',
            'class', 'section', 'teacher', 'pupil',
            # Business data
            'sales', 'revenue', 'profit', 'cost', 'price', 'quantity',
            'units', 'orders', 'customers', 'views', 'clicks',
            # Healthcare data
            'bmi', 'heart_rate', 'blood_pressure', 'cholesterol',
            'glucose', 'temperature', 'weight', 'height',
            # Manufacturing data
            'temperature', 'pressure', 'humidity', 'speed',
            'efficiency', 'defects', 'quality', 'oee',
            # Finance data
            'stock_price', 'volume', 'return', 'dividend',
            'interest_rate', 'inflation', 'gdp'
        ]
        # ──────────────────────────────────────────────────────────

        time_keywords = [
            "date", "time", "timestamp", "datetime",
            "period", "month", "year", "day", "hour",
            "created", "updated", "recorded", "at",
            "when", "start", "end", "logged"
        ]

        candidates = set()

        for col in df.columns:
            col_lower = col.lower()
            if col_lower in EXCLUDE_COLUMNS:
                continue
            if any(kw in col_lower for kw in time_keywords):
                candidates.add(col)

        for col in profile.text_columns:
            col_lower = col.lower()
            if col_lower in EXCLUDE_COLUMNS:
                continue
            candidates.add(col)

        for col in candidates:
            if col not in df.columns:
                continue

            try:
                # ─── REMOVED infer_datetime_format ──────────────────
                parsed = pd.to_datetime(
                    df[col],
                    errors="coerce"
                )
                # ──────────────────────────────────────────────────

                valid_count = parsed.notna().sum()
                valid_ratio = valid_count / len(parsed)

                if valid_ratio >= self.DATETIME_VALID_RATIO_REQUIRED:

                    df[col] = parsed

                    profile.has_time_series  = True
                    profile.time_column      = col
                    profile.time_range_start = str(parsed.min())
                    profile.time_range_end   = str(parsed.max())

                    # ── CRITICAL FIX ──────────────────────────────
                    if col in profile.numeric_columns:
                        profile.numeric_columns.remove(col)
                        logger.info(
                            f"Time column '{col}' removed from "
                            f"numeric_columns after datetime confirmation."
                        )

                    if col in profile.text_columns:
                        profile.text_columns.remove(col)
                        logger.info(
                            f"Time column '{col}' removed from "
                            f"text_columns after datetime confirmation."
                        )

                    if col not in profile.datetime_columns:
                        profile.datetime_columns.append(col)
                        logger.info(
                            f"Time column '{col}' added to "
                            f"datetime_columns."
                        )

                    logger.info(
                        f"Time series confirmed: "
                        f"column='{col}' | "
                        f"range={profile.time_range_start} "
                        f"to {profile.time_range_end} | "
                        f"valid_ratio={valid_ratio:.2f}"
                    )
                    break

            except Exception as error:
                logger.debug(
                    f"Datetime parse attempt failed for "
                    f"'{col}': {error}"
                )
                continue

    # ════════════════════════════════════════════════════
    # POST-DETECTION VALIDATION
    # ════════════════════════════════════════════════════

    def _validate_column_classifications(
        self,
        profile: DatasetProfile
    ) -> None:
        """
        Enforce mutual exclusivity across the three
        column classification lists after all detection
        and reclassification steps have completed.

        A column must appear in exactly one of:
            numeric_columns
            text_columns
            datetime_columns

        Any column found in more than one list is a
        classification conflict that would cause
        downstream components to process it incorrectly.
        This validation step catches and resolves any
        remaining conflicts before the profile is
        handed to the statistical analyzer.

        Conflicts are resolved by priority:
            datetime_columns wins over numeric_columns
            datetime_columns wins over text_columns
            numeric_columns wins over text_columns
        """

        datetime_set = set(profile.datetime_columns)
        numeric_set  = set(profile.numeric_columns)
        text_set     = set(profile.text_columns)

        # Datetime columns must not appear in numeric or text
        conflicts_numeric_datetime = datetime_set & numeric_set
        if conflicts_numeric_datetime:
            for col in conflicts_numeric_datetime:
                profile.numeric_columns.remove(col)
                logger.warning(
                    f"Classification conflict resolved: "
                    f"'{col}' removed from numeric_columns "
                    f"because it is a confirmed datetime column."
                )

        conflicts_text_datetime = datetime_set & text_set
        if conflicts_text_datetime:
            for col in conflicts_text_datetime:
                profile.text_columns.remove(col)
                logger.warning(
                    f"Classification conflict resolved: "
                    f"'{col}' removed from text_columns "
                    f"because it is a confirmed datetime column."
                )

        # Numeric columns must not appear in text columns
        conflicts_numeric_text = numeric_set & text_set
        if conflicts_numeric_text:
            for col in conflicts_numeric_text:
                profile.text_columns.remove(col)
                logger.warning(
                    f"Classification conflict resolved: "
                    f"'{col}' removed from text_columns "
                    f"because it is classified as numeric."
                )

        logger.info(
            f"Column classification validated: "
            f"{len(profile.numeric_columns)} numeric | "
            f"{len(profile.text_columns)} text | "
            f"{len(profile.datetime_columns)} datetime | "
            f"no conflicts remaining"
        )

    # ════════════════════════════════════════════════════
    # PROFILE SUMMARY
    # ════════════════════════════════════════════════════

    def get_profile_summary(
        self,
        profile: DatasetProfile
    ) -> str:
        """
        Generate a human-readable summary of the dataset
        profile for display in the terminal interface
        and Telegram delivery. Concise enough to read
        in under thirty seconds, comprehensive enough
        to confirm the loader understood the structure
        correctly before committing to the full pipeline.
        """

        if not profile.load_success:
            return (
                f"LOAD FAILED\n"
                f"{'─' * 45}\n"
                f"Error: {profile.load_error}"
            )

        lines = [
            "DATASET PROFILE",
            "=" * 50,
            "",
            "FILE",
            f"  Name         : {profile.file_name}",
            f"  Format       : {profile.file_format.upper()}",
            f"  Size         : {profile.file_size_kb} KB",
            f"  Loaded at    : {profile.loaded_at}",
            "",
            "STRUCTURE",
            f"  Rows         : {profile.total_rows:,}",
            f"  Columns      : {profile.total_columns}",
            f"  Numeric      : {len(profile.numeric_columns)}",
            f"  Text         : {len(profile.text_columns)}",
            f"  Datetime     : {len(profile.datetime_columns)}",
            "",
            "DATA QUALITY",
            f"  Completeness : {profile.completeness_percent}%",
            f"  Missing vals : {profile.total_missing_values:,}",
            f"  Duplicates   : {profile.duplicate_rows}",
        ]

        if profile.has_time_series:
            lines += [
                "",
                "TIME SERIES",
                f"  Column       : {profile.time_column}",
                f"  Start        : {profile.time_range_start}",
                f"  End          : {profile.time_range_end}",
            ]

        if profile.numeric_columns:
            lines += ["", "NUMERIC COLUMNS"]
            for col in profile.numeric_columns:
                lines.append(f"  • {col}")

        if profile.text_columns:
            lines += ["", "TEXT COLUMNS"]
            for col in profile.text_columns:
                lines.append(f"  • {col}")

        if profile.datetime_columns:
            lines += ["", "DATETIME COLUMNS"]
            for col in profile.datetime_columns:
                lines.append(f"  • {col}")

        if profile.missing_by_column:
            lines += ["", "MISSING VALUES BY COLUMN"]
            for col, count in sorted(
                profile.missing_by_column.items(),
                key=lambda x: x[1],
                reverse=True
            ):
                pct = round(
                    count / profile.total_rows * 100, 1
                )
                lines.append(
                    f"  • {col}: {count} missing ({pct}%)"
                )

        if profile.warnings:
            lines += ["", "PROCESSING NOTES"]
            for warning in profile.warnings:
                lines.append(f"  ⚠  {warning}")

        lines += ["", "=" * 50]
        return "\n".join(lines)