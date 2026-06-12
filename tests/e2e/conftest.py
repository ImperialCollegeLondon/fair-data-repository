"""Global test fixtures for end-to-end tests."""

import json
from pathlib import Path
from urllib.parse import urlencode

import pytest
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

pytest.base_url = "https://127.0.0.1:5000"

ARTIFACTS_DIR = Path("artifacts")
ARTIFACTS_DIR.mkdir(exist_ok=True)

DEPOSITOR_EMAIL = "test.user@test.co"
REVIEWER_EMAIL = "test.superuser@test.co"
TEST_PASSWORD = "password"


def dump_upload_debug(driver, uploaded_filename):
    """Helper function to dump debug information about the upload page."""
    prefix = ARTIFACTS_DIR / "upload_failed"
    driver.get_full_page_screenshot_as_file(str(prefix.with_suffix(".png")))
    prefix.with_suffix(".html").write_text(driver.page_source, encoding="utf-8")

    submit_buttons = driver.find_elements(
        By.XPATH, "//button[normalize-space()='Submit for review']"
    )
    submit_enabled = submit_buttons[0].is_enabled() if submit_buttons else False
    submit_disabled_attr = (
        submit_buttons[0].get_attribute("disabled") if submit_buttons else "missing"
    )

    row_count = len(
        driver.find_elements(
            By.XPATH,
            f"//tr[.//a[contains(@href, '/draft/files/{uploaded_filename}/content')]]",
        )
    )
    upload_links = [
        el.get_attribute("href")
        for el in driver.find_elements(
            By.XPATH,
            f"//a[contains(@href, '/draft/files/{uploaded_filename}/content')]",
        )
    ]
    progress_nodes = driver.find_elements(By.CSS_SELECTOR, ".file-upload-progress")
    progress_dump = [
        {
            "class": n.get_attribute("class"),
            "data_percent": n.get_attribute("data-percent"),
            "text": n.text.strip(),
        }
        for n in progress_nodes
    ]
    upload_trace = driver.execute_script("return window.__uploadTrace || [];")
    upload_trace_json = json.dumps(
        upload_trace, ensure_ascii=True, default=str, indent=2
    )

    prefix.with_suffix(".txt").write_text(
        "\n".join(
            [
                f"url={driver.current_url}",
                f"row_count={row_count}",
                f"submit_button_count={len(submit_buttons)}",
                f"submit_enabled={submit_enabled}",
                f"submit_disabled_attr={submit_disabled_attr}",
                f"progress_nodes={progress_dump}",
                f"upload_links={upload_links}",
                "upload_trace_json_start",
                upload_trace_json,
            ]
        ),
        encoding="utf-8",
    )


def logout(driver):
    """Helper function to log out the current user."""
    driver.get(f"{pytest.base_url}/logout")
    WebDriverWait(driver, timeout=10).until(
        lambda d: d.current_url == f"{pytest.base_url}/"
        and "user-profile-dropdown-btn" not in d.page_source
        and "Log in" in d.page_source
    )


def login(driver, email, password, next_url="/"):
    """Helper function to log in a user."""
    logout(driver)

    login_query = urlencode({"next": next_url})
    driver.get(f"{pytest.base_url}/login/?{login_query}")

    WebDriverWait(driver, timeout=15).until(
        EC.visibility_of_element_located((By.ID, "email"))
    )
    driver.find_element(By.ID, "email").send_keys(email)
    driver.find_element(By.ID, "password").send_keys(password)
    driver.find_element(By.XPATH, "//button[normalize-space()='Log in']").click()


def create_submission_and_get_request_url(driver):
    """Helper function to create a submission and return the request URL."""
    login(driver, DEPOSITOR_EMAIL, TEST_PASSWORD, next_url="/uploads/new?community=icl")

    WebDriverWait(driver, timeout=10).until(
        lambda d: d.current_url.endswith("uploads/new?community=icl")
    )

    driver.find_element(By.ID, "metadata.title").send_keys("Test Submission")
    driver.find_element(By.ID, "metadata.description").send_keys(
        "This is a test submission."
    )

    driver.find_element(By.XPATH, "//button[normalize-space()='Add creator']").click()
    WebDriverWait(driver, timeout=10).until(
        lambda d: d.find_element(By.ID, "person_or_org.family_name").is_displayed()
    )
    driver.find_element(By.ID, "person_or_org.family_name").send_keys("Test")
    driver.find_element(By.XPATH, "//button[normalize-space()='Save']").click()

    # Wait for modal field to disappear (stronger than generic ".ui.modal.visible")
    WebDriverWait(driver, timeout=15).until(
        EC.invisibility_of_element_located((By.ID, "person_or_org.family_name"))
    )

    dummy_file_path = (Path(__file__).parent / "fixtures/dummy_file.txt").resolve()
    uploaded_filename = dummy_file_path.name

    # Install browser-side tracing for file upload requests.
    driver.execute_script(
        """
        (function () {
          if (window.__uploadTraceInstalled) return;
          window.__uploadTraceInstalled = true;
          window.__uploadTrace = [];

          function shouldTrack(url) {
            return typeof url === "string" && url.indexOf("/draft/files/") !== -1;
          }

          function nowIso() {
            try {
              return new Date().toISOString();
            } catch (e) {
              return "";
            }
          }

          var origFetch = window.fetch;
          if (origFetch) {
            window.fetch = function () {
              var input = arguments[0];
              var init = arguments[1] || {};
              var url = typeof input === "string" ? input : (input && input.url) || "";
              var method = init.method || "GET";
              if (!shouldTrack(url)) return origFetch.apply(this, arguments);
              return origFetch.apply(this, arguments).then(function (res) {
                window.__uploadTrace.push({
                  api: "fetch",
                  ts: nowIso(),
                  method: method,
                  url: url,
                  status: res.status,
                  ok: res.ok
                });
                return res;
              }).catch(function (err) {
                window.__uploadTrace.push({
                  api: "fetch",
                  ts: nowIso(),
                  method: method,
                  url: url,
                  error: String(err)
                });
                throw err;
              });
            };
          }

          var origOpen = XMLHttpRequest.prototype.open;
          var origSend = XMLHttpRequest.prototype.send;
          XMLHttpRequest.prototype.open = function (method, url) {
            this.__traceMethod = method;
            this.__traceUrl = url;
            return origOpen.apply(this, arguments);
          };
          XMLHttpRequest.prototype.send = function () {
            var xhr = this;
            if (shouldTrack(xhr.__traceUrl)) {
              xhr.addEventListener("loadend", function () {
                window.__uploadTrace.push({
                  api: "xhr",
                  ts: nowIso(),
                  method: xhr.__traceMethod || "GET",
                  url: xhr.__traceUrl || "",
                  status: xhr.status
                });
              });
            }
            return origSend.apply(this, arguments);
          };
        })();
        """
    )

    file_input = WebDriverWait(driver, timeout=15).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file']"))
    )
    file_input.send_keys(str(dummy_file_path))

    def upload_completed(d):
        row = d.find_element(
            By.XPATH,
            f"//tr[.//a[contains(@href, '/draft/files/{uploaded_filename}/content')]]",
        )
        progress = row.find_element(By.CSS_SELECTOR, ".file-upload-progress")
        percent_attr = (progress.get_attribute("data-percent") or "").strip()
        percent_text = (
            progress.find_element(By.CSS_SELECTOR, ".bar .progress").text or ""
        ).strip()
        classes = progress.get_attribute("class") or ""
        is_100 = percent_attr == "100" or percent_text == "100%"
        has_error = "error" in classes
        return is_100 and not has_error

    try:
        WebDriverWait(driver, timeout=60).until(upload_completed)
    except TimeoutException as exc:
        dump_upload_debug(driver, uploaded_filename)
        raise AssertionError("File upload did not reach successful 100% state") from exc

    submit_locator = (By.XPATH, "//button[normalize-space()='Submit for review']")
    submit_btn = WebDriverWait(driver, timeout=30).until(
        EC.element_to_be_clickable(submit_locator)
    )
    submit_btn.click()

    required_checkbox_names = [
        "acceptAccessToRecord",
        "acceptAfterPublishRecord",
        "acceptDepositAgreement",
    ]
    for name in required_checkbox_names:
        checkbox = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, f"input[type='checkbox'][name='{name}']")
            )
        )
        if not checkbox.is_selected():
            driver.execute_script("arguments[0].click();", checkbox)

    final_submit_btn = WebDriverWait(driver, timeout=10).until(
        EC.element_to_be_clickable(
            (By.XPATH, "//button[normalize-space()='Submit record for review']")
        )
    )
    final_submit_btn.click()

    driver.get_full_page_screenshot_as_file(
        str(ARTIFACTS_DIR / "submission_submitted.png")
    )

    WebDriverWait(driver, timeout=20).until(lambda d: "/requests" in d.current_url)
    return driver.current_url


@pytest.fixture
def submission_request_url(driver):
    """Fixture to create a submission and return the request URL."""
    return create_submission_and_get_request_url(driver)


@pytest.fixture
def driver(request):
    """Selenium WebDriver fixture."""
    options = webdriver.FirefoxOptions()
    options.add_argument("--headless")
    options.set_capability("acceptInsecureCerts", True)
    _driver = webdriver.Firefox(options=options)
    _driver.set_window_size(1920, 1080)
    _driver.get(pytest.base_url)

    body = _driver.find_element(By.TAG_NAME, "body")
    wait = WebDriverWait(_driver, timeout=10)
    wait.until(lambda _: body.is_displayed())

    yield _driver

    test_name = request.node.originalname
    screenshot_path = ARTIFACTS_DIR / f"{test_name}.png"
    _driver.get_full_page_screenshot_as_file(str(screenshot_path))

    _driver.quit()
