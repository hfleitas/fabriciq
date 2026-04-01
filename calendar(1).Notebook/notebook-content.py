# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse": "dab98636-1291-4c03-876c-74071a46c00a",
# META       "default_lakehouse_name": "autoclaimsdata",
# META       "default_lakehouse_workspace_id": "c02b4576-1584-40be-9f45-199c6a36437e",
# META       "known_lakehouses": [
# META         {
# META           "id": "dab98636-1291-4c03-876c-74071a46c00a"
# META         }
# META       ]
# META     }
# META   }
# META }

# MARKDOWN ********************

# ## Calendar / Date Dimension Table
# 
# PySpark implementation of the Power Query M calendar table.
# Generates a comprehensive date dimension with calendar, ISO, and fiscal year columns.

# CELL ********************

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql import types as T
from pyspark.sql.window import Window
from datetime import date, datetime, timedelta
import math

spark = SparkSession.builder.getOrCreate()

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ### Parameters
# Adjust these to match your requirements.

# CELL ********************

# ----- Configurable Parameters -----
start_date = date(2020, 1, 1)                        # Calendar start date
current_date = date.today()                           # Today
end_date = date(current_date.year + 2, 12, 31)       # Dynamic end date: 2 years out
fy_start_month = 7                                    # Fiscal year start month (1 = Jan)
wd_start = 1                                          # Weekday start number (0 or 1)
holidays = []                                         # List of holiday dates, e.g. [date(2026,1,1), ...]

# Target lakehouse table
target_table = "calendar_dim"

print(f"Start date : {start_date}")
print(f"End date   : {end_date}")
print(f"Current    : {current_date}")
print(f"FY start mo: {fy_start_month}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ### Generate the date spine

# CELL ********************

# Build a list of all dates from start_date to end_date
# If end_date < current_date, also include current_date
day_count = (end_date - start_date).days + 1
all_dates = [start_date + timedelta(days=i) for i in range(day_count)]
if end_date < current_date and current_date not in all_dates:
    all_dates.append(current_date)

df = spark.createDataFrame([(d,) for d in all_dates], ["Date"])
print(f"Row count: {df.count()}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ### Calendar year, quarter, month, week, and day columns

# CELL ********************

cur_year = current_date.year
cur_month = current_date.month
cur_quarter = (cur_month - 1) // 3 + 1
cur_day_of_year = current_date.timetuple().tm_yday

# Monday = day-of-week 1 in Spark (with dayofweek Sunday=1 .. Saturday=7)
# We'll use date_format 'u' for ISO day-of-week (Mon=1..Sun=7)

df = df.withColumn("Year", F.year("Date").cast(T.IntegerType()))
df = df.withColumn("CurrYearOffset", (F.year("Date") - F.lit(cur_year)).cast(T.IntegerType()))
df = df.withColumn("YearCompleted",
    F.when(F.make_date(F.year("Date"), F.lit(12), F.lit(31)) < F.lit(date(cur_year, 12, 31)), True)
     .otherwise(False))

# --- Quarter ---
df = df.withColumn("QuarterNumber", F.quarter("Date").cast(T.IntegerType()))
df = df.withColumn("Quarter", F.concat(F.lit("Q"), F.col("QuarterNumber")))
df = df.withColumn("StartOfQuarter", F.date_trunc("quarter", F.col("Date")).cast(T.DateType()))
df = df.withColumn("EndOfQuarter",
    F.date_sub(F.add_months(F.date_trunc("quarter", F.col("Date")), 3), 1))
df = df.withColumn("QuarterAndYear",
    F.concat(F.lit("Q"), F.col("QuarterNumber").cast("string"), F.lit(" "), F.year("Date").cast("string")))
df = df.withColumn("QuarternYear", (F.year("Date") * 10 + F.quarter("Date")).cast(T.IntegerType()))
df = df.withColumn("CurrQuarterOffset",
    ((4 * F.year("Date") + F.quarter("Date")) - F.lit(4 * cur_year + cur_quarter)).cast(T.IntegerType()))
df = df.withColumn("QuarterCompleted",
    F.when(F.date_sub(F.add_months(F.date_trunc("quarter", F.col("Date")), 3), 1) <
           F.lit(date(cur_year, ((cur_quarter - 1) * 3 + 3), 1) + timedelta(days=-1) + timedelta(days=(
               (date(cur_year, ((cur_quarter - 1) * 3 + 3) % 12 + 1, 1) if (cur_quarter - 1) * 3 + 3 < 12
                else date(cur_year + 1, 1, 1)) -
               date(cur_year, (cur_quarter - 1) * 3 + 1, 1)).days - 1)),
           True).otherwise(False))

# Simpler QuarterCompleted: end of row's quarter < end of current quarter
cur_qtr_end = date(cur_year, cur_quarter * 3, 1)
cur_qtr_end = date(cur_year + (1 if cur_quarter == 4 else 0),
                   (cur_quarter * 3 % 12) + 1, 1) - timedelta(days=1)
df = df.drop("QuarterCompleted")
df = df.withColumn("QuarterCompleted",
    F.when(F.date_sub(F.add_months(F.date_trunc("quarter", F.col("Date")), 3), 1) < F.lit(cur_qtr_end), True)
     .otherwise(False))

# --- Month ---
df = df.withColumn("Month", F.month("Date").cast(T.IntegerType()))
df = df.withColumn("StartOfMonth", F.date_trunc("month", F.col("Date")).cast(T.DateType()))
df = df.withColumn("EndOfMonth", F.last_day("Date"))
df = df.withColumn("MonthAndYear", F.date_format("Date", "MMM yyyy"))
df = df.withColumn("MonthnYear", (F.year("Date") * 100 + F.month("Date")).cast(T.IntegerType()))
df = df.withColumn("CurrMonthOffset",
    ((12 * F.year("Date") + F.month("Date")) - F.lit(12 * cur_year + cur_month)).cast(T.IntegerType()))
cur_month_end = (date(cur_year, cur_month % 12 + 1, 1) if cur_month < 12 else date(cur_year + 1, 1, 1)) - timedelta(days=1)
df = df.withColumn("MonthCompleted",
    F.when(F.last_day("Date") < F.lit(cur_month_end), True).otherwise(False))
df = df.withColumn("MonthName", F.date_format("Date", "MMMM"))
df = df.withColumn("MonthShort", F.date_format("Date", "MMM"))
df = df.withColumn("MonthInitial", F.substring(F.date_format("Date", "MMMM"), 1, 1))
df = df.withColumn("DayOfMonth", F.dayofmonth("Date").cast(T.IntegerType()))

print("Calendar year/quarter/month columns added.")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# --- ISO Week Number (ISO 8601) ---
# Spark's weekofyear follows ISO 8601
df = df.withColumn("WeekNumber", F.weekofyear("Date").cast(T.IntegerType()))

# Start of week (Monday)
# dayofweek returns Sun=1..Sat=7; convert to ISO: Mon=1..Sun=7
df = df.withColumn("_iso_dow", ((F.dayofweek("Date") + 5) % 7 + 1).cast(T.IntegerType()))
df = df.withColumn("StartOfWeek", F.date_sub(F.col("Date"), F.col("_iso_dow") - 1))
df = df.withColumn("EndOfWeek", F.date_add(F.col("StartOfWeek"), 6))
# ISO year for the week (Thursday rule)
df = df.withColumn("_thursday", F.date_add(F.col("StartOfWeek"), 3))
df = df.withColumn("ISOYear", F.year("_thursday").cast(T.IntegerType()))

df = df.withColumn("WeekAndYear",
    F.concat(F.lit("W"), F.lpad(F.col("WeekNumber").cast("string"), 2, "0"),
             F.lit(" "), F.col("ISOYear").cast("string")))
df = df.withColumn("WeeknYear", (F.col("ISOYear") * 100 + F.col("WeekNumber")).cast(T.IntegerType()))

# Week offset from current week
cur_iso_dow = current_date.isoweekday()  # Mon=1..Sun=7
cur_start_of_week = current_date - timedelta(days=cur_iso_dow - 1)
cur_start_of_week_num = cur_start_of_week.toordinal()
df = df.withColumn("CurrWeekOffset",
    ((F.datediff(F.col("StartOfWeek"), F.lit(cur_start_of_week))) / 7).cast(T.IntegerType()))

cur_end_of_week = cur_start_of_week + timedelta(days=6)
df = df.withColumn("WeekCompleted",
    F.when(F.col("EndOfWeek") < F.lit(cur_end_of_week), True).otherwise(False))

# --- Day of Week ---
# M code: Date.DayOfWeek([Date], Day.Monday) + WDStart
# Day.Monday base => Mon=0, Tue=1 .. Sun=6;  WDStart=1 => Mon=1..Sun=7
df = df.withColumn("DayOfWeekNumber",
    (F.col("_iso_dow") - 1 + F.lit(wd_start)).cast(T.IntegerType()))
df = df.withColumn("DayOfWeekName", F.date_format("Date", "EEEE"))
df = df.withColumn("DayOfWeekInitial", F.substring(F.date_format("Date", "EEEE"), 1, 1))
df = df.withColumn("DayOfYear", F.dayofyear("Date").cast(T.IntegerType()))

df = df.withColumn("DateInt",
    (F.year("Date") * 10000 + F.month("Date") * 100 + F.dayofmonth("Date")).cast(T.IntegerType()))
df = df.withColumn("CurrDayOffset",
    F.datediff(F.col("Date"), F.lit(current_date)).cast(T.IntegerType()))
df = df.withColumn("IsAfterToday", F.col("Date") > F.lit(current_date))
df = df.withColumn("IsWeekDay",
    F.when(F.col("_iso_dow") <= 5, True).otherwise(False))

# --- Holiday / Business Day ---
if holidays:
    holidays_set = set(holidays)
    is_holiday_udf = F.udf(lambda d: d in holidays_set if d else False, T.BooleanType())
    df = df.withColumn("IsHoliday", is_holiday_udf(F.col("Date")))
else:
    df = df.withColumn("IsHoliday", F.lit("Unknown"))

df = df.withColumn("IsBusinessDay",
    F.when((F.col("IsWeekDay") == True) & (F.col("IsHoliday") != True), True).otherwise(False))

df = df.withColumn("DayType",
    F.when(F.col("IsHoliday") == True, "Holiday")
     .when(F.col("IsWeekDay") == False, "Weekend")
     .when(F.col("IsWeekDay") == True, "Weekday"))

print("Week and day columns added.")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ### ISO year / quarter columns

# CELL ********************

# ISO Year already computed above via Thursday rule
cur_iso_year = current_date.isocalendar()[0]
cur_iso_week = current_date.isocalendar()[1]
cur_iso_qtr = (1 if cur_iso_week <= 13 else 2 if cur_iso_week <= 26 else 3 if cur_iso_week <= 39 else 4)

df = df.withColumn("ISOCurrYearOffset", (F.col("ISOYear") - F.lit(cur_iso_year)).cast(T.IntegerType()))

df = df.withColumn("ISOQuarterNumber",
    F.when(F.col("WeekNumber") > 39, 4)
     .when(F.col("WeekNumber") > 26, 3)
     .when(F.col("WeekNumber") > 13, 2)
     .otherwise(1).cast(T.IntegerType()))
df = df.withColumn("ISOQuarter", F.concat(F.lit("Q"), F.col("ISOQuarterNumber").cast("string")))
df = df.withColumn("ISOQuarterAndYear",
    F.concat(F.lit("Q"), F.col("ISOQuarterNumber").cast("string"), F.lit(" "), F.col("ISOYear").cast("string")))
df = df.withColumn("ISOQuarternYear",
    (F.col("ISOYear") * 10 + F.col("ISOQuarterNumber")).cast(T.IntegerType()))
df = df.withColumn("ISOCurrQuarterOffset",
    ((4 * F.col("ISOYear") + F.col("ISOQuarterNumber")) - F.lit(4 * cur_iso_year + cur_iso_qtr)).cast(T.IntegerType()))

print("ISO columns added.")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ### Fiscal year, quarter, period, and week columns

# CELL ********************

fys = fy_start_month  # alias for readability

# Fiscal Year label: if FYStartMonth > 1 and Month >= FYStartMonth then Year+1 else Year
df = df.withColumn("_fy_year_num",
    F.when((F.lit(fys) > 1) & (F.month("Date") >= F.lit(fys)), F.year("Date") + 1)
     .otherwise(F.year("Date")))
df = df.withColumn("FiscalYear", F.concat(F.lit("FY"), F.col("_fy_year_num").cast("string")))

# Fiscal Quarter
df = df.withColumn("_fiscal_month",
    F.month(F.add_months(F.col("Date"), -(fys - 1))))
df = df.withColumn("_fq_num", F.ceil(F.col("_fiscal_month") / 3).cast(T.IntegerType()))
df = df.withColumn("FiscalQuarter",
    F.concat(F.lit("FQ"), F.col("_fq_num").cast("string"), F.lit(" "), F.col("_fy_year_num").cast("string")))
df = df.withColumn("FQuarternYear",
    (F.col("_fy_year_num") * 10 + F.col("_fq_num")).cast(T.IntegerType()))

# Fiscal Period Number
df = df.withColumn("FiscalPeriodNumber",
    F.when((F.month("Date") >= F.lit(fys)) & (F.lit(fys) > 1), F.month("Date") - (fys - 1))
     .when((F.month("Date") >= F.lit(fys)) & (F.lit(fys) == 1), F.month("Date"))
     .otherwise(F.month("Date") + (12 - fys + 1))
     .cast(T.IntegerType()))

df = df.withColumn("FiscalPeriod",
    F.concat(F.lit("FP"), F.lpad(F.col("FiscalPeriodNumber").cast("string"), 2, "0"),
             F.lit(" "), F.col("_fy_year_num").cast("string")))
df = df.withColumn("FPeriodnYear",
    (F.col("_fy_year_num") * 100 + F.col("FiscalPeriodNumber")).cast(T.IntegerType()))

# Fiscal CurrYearOffset
cur_fy_year_num = (cur_year + 1) if (fys > 1 and cur_month >= fys) else cur_year
df = df.withColumn("FiscalCurrYearOffset",
    (F.col("_fy_year_num") - F.lit(cur_fy_year_num)).cast(T.IntegerType()))

# Current FY / FQ / FP flags
cur_fy_label = f"FY{cur_fy_year_num}"
cur_fq_num = math.ceil(((cur_month - fys) % 12 + 1) / 3) if fys == 1 else math.ceil(
    ((cur_month - fys + 12) % 12 + 1) / 3) if cur_month < fys else math.ceil((cur_month - fys + 1) / 3)
cur_fq_n_year = cur_fy_year_num * 10 + cur_fq_num
cur_fp_num = (cur_month - fys + 1) if cur_month >= fys else (cur_month + 12 - fys + 1)
cur_fp_n_year = cur_fy_year_num * 100 + cur_fp_num

df = df.withColumn("IsCurrentFY", F.col("FiscalYear") == F.lit(cur_fy_label))
df = df.withColumn("IsCurrentFQ", F.col("FQuarternYear") == F.lit(cur_fq_n_year))
df = df.withColumn("IsCurrentFP", F.col("FPeriodnYear") == F.lit(cur_fp_n_year))

print("Fiscal year/quarter/period columns added.")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# --- Fiscal Week ---
# Build a fiscal-week lookup: for each fiscal year, number the ISO-weeks sequentially
from pyspark.sql.window import Window

if fys == 1:
    # When FY starts in January, fiscal week = ISO week
    df = df.withColumn("FiscalWeekNumber", F.col("WeekNumber"))
else:
    # Group weeks within each fiscal year and number them
    fw_window = Window.partitionBy("_fy_year_num").orderBy("StartOfWeek", "Date")
    df = df.withColumn("_fw_rank",
        F.dense_rank().over(Window.partitionBy("_fy_year_num").orderBy("StartOfWeek")))
    df = df.withColumn("FiscalWeekNumber", F.col("_fw_rank").cast(T.IntegerType()))
    df = df.drop("_fw_rank")

# Fiscal Week label
df = df.withColumn("FiscalWeek",
    F.concat(F.lit("FW"), F.lpad(F.col("FiscalWeekNumber").cast("string"), 2, "0"),
             F.lit(" "), F.col("_fy_year_num").cast("string")))

df = df.withColumn("FWeeknYear",
    (F.col("_fy_year_num") * 100 + F.col("FiscalWeekNumber")).cast(T.IntegerType()))

# IsCurrentFW
cur_fw_row = df.filter(F.col("Date") == F.lit(current_date)).select("FWeeknYear").first()
cur_fw_n_year = cur_fw_row[0] if cur_fw_row else 0
df = df.withColumn("IsCurrentFW", F.col("FWeeknYear") == F.lit(cur_fw_n_year))

print("Fiscal week columns added.")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ### Prior-year-to-date and prior-fiscal-year-to-date flags

# CELL ********************

# IsPYTD: same day-of-year range in the prior calendar year
df = df.withColumn("IsPYTD",
    F.when((F.year("Date") == F.lit(cur_year - 1)) &
           (F.dayofyear("Date") <= F.lit(cur_day_of_year)), True)
     .otherwise(False))

# IsPFYTD: same relative position in the prior fiscal year
# Fiscal first day for current FY
if fys > 1 and cur_month >= fys:
    cur_fiscal_first = date(cur_year, fys, 1)
elif fys > 1:
    cur_fiscal_first = date(cur_year - 1, fys, 1)
else:
    cur_fiscal_first = date(cur_year, 1, 1)

days_into_fy = (current_date - cur_fiscal_first).days  # how many days into the current FY
prev_fiscal_first = date(cur_fiscal_first.year - 1, cur_fiscal_first.month, cur_fiscal_first.day)
prev_fy_cutoff = prev_fiscal_first + timedelta(days=days_into_fy)

df = df.withColumn("IsPFYTD",
    F.when((F.col("FiscalCurrYearOffset") == -1) &
           (F.col("Date") >= F.lit(prev_fiscal_first)) &
           (F.col("Date") <= F.lit(prev_fy_cutoff)), True)
     .otherwise(False))

print("PYTD and PFYTD flags added.")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ### Select and reorder final columns

# CELL ********************

final_columns = [
    "Date",
    "Year", "CurrYearOffset", "YearCompleted",
    "QuarterNumber", "Quarter", "StartOfQuarter", "EndOfQuarter",
    "QuarterAndYear", "QuarternYear", "CurrQuarterOffset", "QuarterCompleted",
    "Month", "StartOfMonth", "EndOfMonth",
    "MonthAndYear", "MonthnYear", "CurrMonthOffset", "MonthCompleted",
    "MonthName", "MonthShort", "MonthInitial", "DayOfMonth",
    "WeekNumber", "StartOfWeek", "EndOfWeek",
    "WeekAndYear", "WeeknYear", "CurrWeekOffset", "WeekCompleted",
    "DayOfWeekNumber", "DayOfWeekName", "DayOfWeekInitial",
    "DateInt", "CurrDayOffset", "IsAfterToday", "IsWeekDay",
    "IsHoliday", "IsBusinessDay", "DayType",
    "ISOYear", "ISOCurrYearOffset",
    "ISOQuarterNumber", "ISOQuarter", "ISOQuarterAndYear",
    "ISOQuarternYear", "ISOCurrQuarterOffset",
    "FiscalYear", "FiscalCurrYearOffset",
    "FiscalQuarter", "FQuarternYear",
    "FiscalPeriodNumber", "FiscalPeriod", "FPeriodnYear",
    "FiscalWeekNumber", "FiscalWeek", "FWeeknYear",
    "IsCurrentFY", "IsCurrentFQ", "IsCurrentFP", "IsCurrentFW",
    "IsPYTD", "IsPFYTD"
]

df_final = df.select(*final_columns).orderBy("Date")

print(f"Final column count: {len(final_columns)}")
df_final.show(5, truncate=False)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ### Write to lakehouse table

# CELL ********************

df_final.write.mode("overwrite").format("delta").saveAsTable(target_table)
print(f"Table '{target_table}' written successfully with {df_final.count()} rows.")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
