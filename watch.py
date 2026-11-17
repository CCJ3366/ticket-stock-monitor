import json
from urllib.parse import urljoin, urlsplit

from playwright.sync_api import sync_playwright

URL = "https://clubz.cloudsation.com/event/3983.html?userid="


def check_stock(page):
    response = page.goto(URL, wait_until="domcontentloaded", timeout=30000)
    if response is None or not response.ok:
        raise RuntimeError("票务页加载失败")
    page.locator("a.sub-event-item").first.wait_for(timeout=20000)
    tickets = page.locator("a.sub-event-item")
    for i in range(tickets.count()):
        ticket = tickets.nth(i)

        def get_text(selector):
            element = ticket.locator(selector)
            return element.first.inner_text().strip() if element.count() else ""

        date = get_text(".start-time")
        name = get_text(".stu")
        price = get_text(".price")
        show_time = get_text(".time")
        if (
            date == "12-11"
            and name == "学生票盲盒"
            and price == "￥199"
            and show_time == "19:30"
        ):
            classes = (ticket.get_attribute("class") or "").split()
            href = (ticket.get_attribute("href") or "").strip()
            if "disabled" in classes and href == "javascript:void(0)":
                return False, None
            if "disabled" not in classes and href:
                link = urljoin(URL, href)
                purchase = urlsplit(link)
                if (
                    purchase.scheme == "https"
                    and purchase.netloc == urlsplit(URL).netloc
                    and purchase.path in {"/event/ticket.html", "/event/ticketunseat.html"}
                ):
                    return True, link
            raise RuntimeError("发现目标票档，但链接状态未知")
    raise RuntimeError("未找到12月11日目标票档，无法判断库存")


def main():
    with sync_playwright() as p:
        with p.chromium.launch(headless=True) as browser:
            page = browser.new_page(locale="zh-CN", timezone_id="Asia/Shanghai")
            in_stock, link = check_stock(page)

    # 输出单条检测结果，供工作流读取。
    print(json.dumps({"in_stock": in_stock, "ticket_url": link}))


if __name__ == "__main__":
    main()
