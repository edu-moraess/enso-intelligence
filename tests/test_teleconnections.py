from src.noaa.teleconnections import parse_mjo, parse_olr, parse_psl


def test_mjo_parser_extracts_rmm_fields():
    sample = """RMM values up to "real time".
 year, month, day, RMM1, RMM2, phase, amplitude.
 2026 09 20 1.25 -0.50 5 1.35 WH04_method:_OLR_&_NCEP_wind
"""
    df = parse_mjo(sample)
    assert list(df.columns) == ["date", "rmm1", "rmm2", "phase", "amplitude"]
    assert df.iloc[0]["phase"] == 5
    assert round(float(df.iloc[0]["amplitude"]), 2) == 1.35


def test_olr_parser_uses_anomaly_section_and_compact_missing_values():
    sample = """OUTGOING LONG WAVE RADIATION EQUATOR/160E-160W
 ORIGINAL DATA
 YEAR JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC
 2025 61.7 65.8 64.0 46.3 49.8 51.9 48.2 63.3 66.8 64.5 55.1 54.8
 OUTGOING LONG WAVE RADIATION EQUATOR/160E-160W
 ANOMALY
 YEAR JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC
 2025 26.9 30.9 27.0 9.0 7.1 8.2 2.1 12.7 12.9 12.5 7.3 17.7
 2026 7.9 18.2 5.6 5.3 -1.8 -17.9 -19.4 -14.9-999.9-999.9-999.9-999.9
"""
    df = parse_olr(sample)
    assert df.iloc[0]["olr"] == 26.9
    assert df.iloc[-1]["date"].strftime("%Y-%m") == "2026-08"
    assert len(df) == 20


def test_psl_parser_reads_standard_monthly_rows():
    sample = """2000 2001
2000  0.100  0.200  -0.300  0.400  0.500  0.600  0.700  0.800  0.900  1.000  1.100  1.200
2001 -0.100 -0.200 -0.300 -0.400 -0.500 -0.600 -0.700 -0.800 -0.900 -1.000 -1.100 -1.200
-999
"""
    df = parse_psl(sample, "pdo")
    assert len(df) == 24
    assert df.iloc[0]["pdo"] == 0.1
    assert df.iloc[-1]["pdo"] == -1.2
