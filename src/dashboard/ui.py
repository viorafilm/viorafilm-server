from decimal import Decimal, ROUND_HALF_UP
from urllib.parse import urlencode

from django.urls import reverse


SUPPORTED_DASHBOARD_LANGS = ("ko", "en")
SUPPORTED_BILLING_CURRENCIES = ("KRW", "USD", "AED", "EUR")

_CURRENCY_META = {
    "KRW": {"krw_per_unit": Decimal("1"), "decimals": 0, "label": "KRW"},
    "USD": {"krw_per_unit": Decimal("1400"), "decimals": 2, "label": "USD"},
    "AED": {"krw_per_unit": Decimal("381"), "decimals": 2, "label": "AED"},
    "EUR": {"krw_per_unit": Decimal("1520"), "decimals": 2, "label": "EUR"},
}

_UI_TEXT = {
    "ko": {
        "base": {
            "subtitle": "Kiosk Control Center",
            "page_title": "운영 대시보드",
            "menu_button": "메뉴",
            "language": "언어",
            "lang_ko": "한국어",
            "lang_en": "English",
            "menu_index": "매출 현황",
            "menu_devices": "장치 관리",
            "menu_ops": "관측성",
            "menu_billing": "수금 관리",
            "menu_sales": "매출 관리",
            "menu_coupons": "쿠폰 관리",
            "menu_photos": "사진 관리",
            "change_password": "비밀번호 변경",
            "logout": "로그아웃",
        },
        "login": {
            "subtitle": "관리자 로그인",
            "invalid_credentials": "아이디 또는 비밀번호가 올바르지 않습니다.",
            "username": "아이디",
            "password": "비밀번호",
            "submit": "로그인",
        },
        "index": {
            "today_total": "오늘 매출",
            "month_total": "이번 달 매출",
            "sales_count": "총 거래 건수",
            "view_devices": "장치 상태 보기",
            "view_ops": "관측성 보기",
            "view_billing": "수금 관리 보기",
            "view_sales": "매출 내역 보기",
            "view_coupons": "쿠폰 관리 보기",
            "view_photos": "사진 관리 보기",
        },
        "billing": {
            "title": "수금 관리",
            "month_summary_prefix": "기준 월",
            "period_prefix": "집계 기간",
            "live_month_suffix": "(현재 월 실시간 누적)",
            "organization": "조직",
            "all_organizations": "전체 조직",
            "branch": "지점",
            "all_branches": "전체 지점",
            "billing_month": "정산 월",
            "display_currency": "표시 통화",
            "apply_filters": "필터 적용",
            "reset_filters": "필터 초기화",
            "previous_month": "이전 달",
            "next_month": "다음 달",
            "branch_count": "브랜치 수",
            "device_count": "활성 장치 수",
            "server_fee_total": "장치 서버비",
            "ai_extra_total": "AI 추가 청구",
            "requested_total": "요청 금액 합계",
            "paid_count": "수금 완료 브랜치",
            "info_prefix": "장치 서버비는 현재 활성 장치 기준으로 1대당",
            "info_suffix": "입니다. AI 추가 청구액은 해당 월 AI 사용량 기준 예상액입니다.",
            "table_org": "조직",
            "table_branch": "지점",
            "table_active_devices": "활성 장치",
            "table_server_fee": "장치 서버비",
            "table_ai_usage": "AI 거래/이미지",
            "table_ai_extra": "AI 추가 청구",
            "table_requested": "요청 금액",
            "table_status": "상태",
            "table_paid_at": "수금 시각",
            "table_note": "메모",
            "table_action": "처리",
            "status_paid": "수금 완료",
            "status_pending": "미수금",
            "placeholder_note": "메모",
            "mark_pending": "미수금",
            "mark_paid": "수금 완료",
            "read_only": "읽기 전용",
            "empty": "표시할 정산 대상이 없습니다.",
            "message_paid": "{branch} {month} 수금 완료로 표시했습니다.",
            "message_pending": "{branch} {month} 미수금으로 표시했습니다.",
            "message_missing_branch": "수금 상태를 변경할 지점을 찾지 못했습니다.",
            "message_unsupported": "지원하지 않는 수금 처리 요청입니다.",
        },
    },
    "en": {
        "base": {
            "subtitle": "Kiosk Control Center",
            "page_title": "Operations Dashboard",
            "menu_button": "Menu",
            "language": "Language",
            "lang_ko": "한국어",
            "lang_en": "English",
            "menu_index": "Overview",
            "menu_devices": "Devices",
            "menu_ops": "Observability",
            "menu_billing": "Billing",
            "menu_sales": "Sales",
            "menu_coupons": "Coupons",
            "menu_photos": "Photos",
            "change_password": "Change Password",
            "logout": "Log Out",
        },
        "login": {
            "subtitle": "Admin Login",
            "invalid_credentials": "Invalid username or password.",
            "username": "Username",
            "password": "Password",
            "submit": "Sign In",
        },
        "index": {
            "today_total": "Today's Sales",
            "month_total": "This Month's Sales",
            "sales_count": "Total Transactions",
            "view_devices": "View Devices",
            "view_ops": "View Observability",
            "view_billing": "View Billing",
            "view_sales": "View Sales",
            "view_coupons": "View Coupons",
            "view_photos": "View Photos",
        },
        "billing": {
            "title": "Billing",
            "month_summary_prefix": "Billing Month",
            "period_prefix": "Period",
            "live_month_suffix": "(month-to-date)",
            "organization": "Organization",
            "all_organizations": "All Organizations",
            "branch": "Branch",
            "all_branches": "All Branches",
            "billing_month": "Billing Month",
            "display_currency": "Display Currency",
            "apply_filters": "Apply Filters",
            "reset_filters": "Reset Filters",
            "previous_month": "Previous Month",
            "next_month": "Next Month",
            "branch_count": "Branches",
            "device_count": "Active Devices",
            "server_fee_total": "Device Server Fee",
            "ai_extra_total": "AI Surcharge",
            "requested_total": "Requested Total",
            "paid_count": "Paid Branches",
            "info_prefix": "Per-device monthly server fee is",
            "info_suffix": ". AI surcharge is estimated from monthly AI usage.",
            "table_org": "Organization",
            "table_branch": "Branch",
            "table_active_devices": "Active Devices",
            "table_server_fee": "Device Fee",
            "table_ai_usage": "AI Sales / Images",
            "table_ai_extra": "AI Surcharge",
            "table_requested": "Requested Total",
            "table_status": "Status",
            "table_paid_at": "Paid At",
            "table_note": "Note",
            "table_action": "Action",
            "status_paid": "Paid",
            "status_pending": "Pending",
            "placeholder_note": "Note",
            "mark_pending": "Mark Pending",
            "mark_paid": "Mark Paid",
            "read_only": "Read-only",
            "empty": "No billing targets found.",
            "message_paid": "Marked {branch} {month} as paid.",
            "message_pending": "Marked {branch} {month} as pending.",
            "message_missing_branch": "Could not find the branch to update.",
            "message_unsupported": "Unsupported billing action.",
        },
    },
}


def resolve_dashboard_lang(request):
    requested = str(request.GET.get("lang") or request.POST.get("lang") or "").strip().lower()
    session_lang = str(getattr(request, "session", {}).get("dashboard_lang", "") or "").strip().lower()
    lang = requested if requested in SUPPORTED_DASHBOARD_LANGS else session_lang
    if lang not in SUPPORTED_DASHBOARD_LANGS:
        lang = "ko"
    if hasattr(request, "session"):
        request.session["dashboard_lang"] = lang
    return lang


def resolve_billing_currency(request):
    requested = str(request.GET.get("currency") or request.POST.get("currency") or "").strip().upper()
    session_currency = str(getattr(request, "session", {}).get("dashboard_billing_currency", "") or "").strip().upper()
    currency = requested if requested in SUPPORTED_BILLING_CURRENCIES else session_currency
    if currency not in SUPPORTED_BILLING_CURRENCIES:
        currency = "KRW"
    if hasattr(request, "session"):
        request.session["dashboard_billing_currency"] = currency
    return currency


def get_dashboard_text(lang):
    return _UI_TEXT.get(lang, _UI_TEXT["ko"])


def build_query_string(params):
    clean = {}
    for key, value in params.items():
        if value in (None, ""):
            continue
        clean[key] = value
    if not clean:
        return ""
    return urlencode(clean)


def build_path_with_query(path, params):
    query = build_query_string(params)
    return f"{path}?{query}" if query else path


def build_dashboard_ui(request):
    lang = resolve_dashboard_lang(request)
    text = get_dashboard_text(lang)
    base = text["base"]
    current_params = request.GET.copy()
    switch_urls = {}
    for target_lang in SUPPORTED_DASHBOARD_LANGS:
        params = current_params.copy()
        params["lang"] = target_lang
        switch_urls[target_lang] = build_path_with_query(request.path, params)
    nav = {
        "index": build_path_with_query(reverse("dashboard_index"), {"lang": lang}),
        "devices": build_path_with_query(reverse("dashboard_devices"), {"lang": lang}),
        "ops": build_path_with_query(reverse("dashboard_ops"), {"lang": lang}),
        "billing": build_path_with_query(reverse("dashboard_billing"), {"lang": lang}),
        "sales": build_path_with_query(reverse("dashboard_sales"), {"lang": lang}),
        "coupons": build_path_with_query(reverse("dashboard_coupons"), {"lang": lang}),
        "photos": build_path_with_query(reverse("dashboard_photos"), {"lang": lang}),
        "password_change": "/admin/password_change/",
    }
    return {
        "lang": lang,
        "text": text,
        "switch_urls": switch_urls,
        "nav": nav,
    }


def get_currency_meta(code):
    return _CURRENCY_META.get(code, _CURRENCY_META["KRW"])


def format_money_from_krw(amount_krw, currency):
    meta = get_currency_meta(currency)
    amount = Decimal(int(amount_krw or 0))
    divisor = meta["krw_per_unit"]
    decimals = int(meta["decimals"])
    if divisor <= 0:
        divisor = Decimal("1")
    converted = amount / divisor
    if decimals <= 0:
        quantized = converted.quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        return f"{int(quantized):,}"
    pattern = "1." + ("0" * decimals)
    quantized = converted.quantize(Decimal(pattern), rounding=ROUND_HALF_UP)
    return f"{quantized:,.{decimals}f}"


def billing_currency_options():
    return [
        {
            "code": code,
            "label": _CURRENCY_META[code]["label"],
        }
        for code in SUPPORTED_BILLING_CURRENCIES
    ]
