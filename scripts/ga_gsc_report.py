"""
GA4 + Search Console レポート取得スクリプト

事前準備:
  pip install google-analytics-data google-api-python-client google-auth

実行:
  python scripts/ga_gsc_report.py                     # 直近28日間
  python scripts/ga_gsc_report.py 7                    # 直近7日間
  python scripts/ga_gsc_report.py 28 sanmeigaku.html   # 指定ページに絞ったクエリ内訳も追加表示
"""
import sys
import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

from google.oauth2 import service_account
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    RunReportRequest, DateRange, Dimension, Metric, OrderBy,
)
from googleapiclient.discovery import build

BASE_DIR = Path(__file__).resolve().parent.parent
KEY_FILE = BASE_DIR / "mygeocodeproject-466612-c924218caa36.json"
GA4_PROPERTY_ID = "543525843"
GSC_SITE_URL = "https://mirai-fortune.github.io/mirai-uranai/"

SCOPES = [
    "https://www.googleapis.com/auth/analytics.readonly",
    "https://www.googleapis.com/auth/webmasters.readonly",
]


def get_credentials():
    return service_account.Credentials.from_service_account_file(str(KEY_FILE), scopes=SCOPES)


def ga4_report(creds, days):
    client = BetaAnalyticsDataClient(credentials=creds)
    date_range = DateRange(start_date=f"{days}daysAgo", end_date="today")

    summary = client.run_report(RunReportRequest(
        property=f"properties/{GA4_PROPERTY_ID}",
        date_ranges=[date_range],
        metrics=[
            Metric(name="sessions"),
            Metric(name="activeUsers"),
            Metric(name="screenPageViews"),
            Metric(name="averageSessionDuration"),
            Metric(name="engagementRate"),
        ],
    ))

    top_pages = client.run_report(RunReportRequest(
        property=f"properties/{GA4_PROPERTY_ID}",
        date_ranges=[date_range],
        dimensions=[Dimension(name="pagePath")],
        metrics=[Metric(name="screenPageViews")],
        order_bys=[OrderBy(metric=OrderBy.MetricOrderBy(metric_name="screenPageViews"), desc=True)],
        limit=10,
    ))

    channels = client.run_report(RunReportRequest(
        property=f"properties/{GA4_PROPERTY_ID}",
        date_ranges=[date_range],
        dimensions=[Dimension(name="sessionDefaultChannelGroup")],
        metrics=[Metric(name="sessions")],
        order_bys=[OrderBy(metric=OrderBy.MetricOrderBy(metric_name="sessions"), desc=True)],
    ))

    devices = client.run_report(RunReportRequest(
        property=f"properties/{GA4_PROPERTY_ID}",
        date_ranges=[date_range],
        dimensions=[Dimension(name="deviceCategory")],
        metrics=[Metric(name="sessions")],
        order_bys=[OrderBy(metric=OrderBy.MetricOrderBy(metric_name="sessions"), desc=True)],
    ))

    regions = client.run_report(RunReportRequest(
        property=f"properties/{GA4_PROPERTY_ID}",
        date_ranges=[date_range],
        dimensions=[Dimension(name="region")],
        metrics=[Metric(name="sessions"), Metric(name="activeUsers")],
        order_bys=[OrderBy(metric=OrderBy.MetricOrderBy(metric_name="sessions"), desc=True)],
        limit=50,
    ))

    return summary, top_pages, channels, devices, regions


def gsc_report(creds, days):
    service = build("searchconsole", "v1", credentials=creds)
    end = datetime.date.today() - datetime.timedelta(days=2)  # GSCは直近2日ほどデータ反映が遅れる
    start = end - datetime.timedelta(days=days)

    totals = service.searchanalytics().query(
        siteUrl=GSC_SITE_URL,
        body={"startDate": str(start), "endDate": str(end)},
    ).execute()

    queries = service.searchanalytics().query(
        siteUrl=GSC_SITE_URL,
        body={"startDate": str(start), "endDate": str(end), "dimensions": ["query"], "rowLimit": 20},
    ).execute()

    pages = service.searchanalytics().query(
        siteUrl=GSC_SITE_URL,
        body={"startDate": str(start), "endDate": str(end), "dimensions": ["page"], "rowLimit": 20},
    ).execute()

    return totals, queries, pages, start, end


def gsc_page_queries(creds, days, page_filter, row_limit=30):
    service = build("searchconsole", "v1", credentials=creds)
    end = datetime.date.today() - datetime.timedelta(days=2)
    start = end - datetime.timedelta(days=days)

    result = service.searchanalytics().query(
        siteUrl=GSC_SITE_URL,
        body={
            "startDate": str(start),
            "endDate": str(end),
            "dimensions": ["query"],
            "dimensionFilterGroups": [{
                "filters": [{"dimension": "page", "operator": "contains", "expression": page_filter}]
            }],
            "rowLimit": row_limit,
        },
    ).execute()
    return result


def fmt_num(v):
    return f"{float(v):,.0f}" if "." not in str(v) or float(v) == int(float(v)) else f"{float(v):,.1f}"


def print_report(days, page_filter=None):
    creds = get_credentials()

    print(f"\n{'='*60}\nGA4 + Search Console レポート（直近{days}日間）\n{'='*60}\n")

    print("--- GA4 サマリー ---")
    summary, top_pages, channels, devices, regions = ga4_report(creds, days)
    row = summary.rows[0].metric_values
    metric_names = ["セッション数", "アクティブユーザー数", "ページビュー数", "平均セッション時間(秒)", "エンゲージメント率"]
    for name, mv in zip(metric_names, row):
        val = mv.value
        print(f"  {name}: {fmt_num(val)}")

    print("\n--- 人気ページ TOP10 ---")
    for r in top_pages.rows:
        print(f"  {r.dimension_values[0].value}  {r.metric_values[0].value}PV")

    print("\n--- 流入チャネル別セッション数 ---")
    for r in channels.rows:
        print(f"  {r.dimension_values[0].value}: {r.metric_values[0].value}")

    print("\n--- デバイス別セッション数 ---")
    for r in devices.rows:
        print(f"  {r.dimension_values[0].value}: {r.metric_values[0].value}")

    print("\n--- 地域別（都道府県）セッション数 ---")
    for r in regions.rows:
        region_name = r.dimension_values[0].value
        print(f"  {region_name}: セッション{r.metric_values[0].value} / ユーザー{r.metric_values[1].value}")

    print("\n--- Search Console ---")
    totals, queries, pages, start, end = gsc_report(creds, days)
    print(f"  集計期間: {start} 〜 {end}（データ反映の遅延を考慮し直近2日を除外）")
    if totals.get("rows"):
        t = totals["rows"][0]
        print(f"  クリック数: {t['clicks']:.0f} / 表示回数: {t['impressions']:.0f} / "
              f"CTR: {t['ctr']*100:.2f}% / 平均掲載順位: {t['position']:.1f}")
    else:
        print("  データなし")

    print("\n--- 検索クエリ TOP20 ---")
    for r in queries.get("rows", []):
        print(f"  {r['keys'][0]}: クリック{r['clicks']:.0f} / 表示{r['impressions']:.0f} / "
              f"CTR{r['ctr']*100:.1f}% / 順位{r['position']:.1f}")

    print("\n--- 検索流入ページ TOP20 ---")
    for r in pages.get("rows", []):
        print(f"  {r['keys'][0]}: クリック{r['clicks']:.0f} / 表示{r['impressions']:.0f} / "
              f"CTR{r['ctr']*100:.1f}% / 順位{r['position']:.1f}")

    if page_filter:
        print(f"\n--- ページ別クエリ内訳: 「{page_filter}」を含むページ ---")
        page_result = gsc_page_queries(creds, days, page_filter)
        rows = page_result.get("rows", [])
        if rows:
            for r in rows:
                print(f"  {r['keys'][0]}: クリック{r['clicks']:.0f} / 表示{r['impressions']:.0f} / "
                      f"CTR{r['ctr']*100:.1f}% / 順位{r['position']:.1f}")
        else:
            print("  データなし（該当ページへの検索流入がこの期間はありません）")

    print()


if __name__ == "__main__":
    days_arg = int(sys.argv[1]) if len(sys.argv) > 1 else 28
    page_arg = sys.argv[2] if len(sys.argv) > 2 else None
    print_report(days_arg, page_arg)
