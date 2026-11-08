from app.scrapers.vidvalic import VidValicScraper


def test_vidvalic_tickera_parser():
    html = """<article class='tc-single-event'><span>10. septembra, 2026</span><span>20:00</span><span class='tc-event-location'>Ljubljana</span></article>"""
    events = VidValicScraper().parse_ajax_html(html, "Dediščina", "https://example.test")
    assert len(events) == 1
    assert events[0].event_time.strftime("%H:%M") == "20:00"
