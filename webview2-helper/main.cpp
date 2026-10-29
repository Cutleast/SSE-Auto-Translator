// Copyright (c) Cutleast. Licensed under the project's GPL-3.0 license.

#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#include <windows.h>
#include <shellapi.h>
#include <dwmapi.h>
#include <wrl.h>
#include <WebView2.h>

#include <ctime>
#include <filesystem>
#include <string>

using Microsoft::WRL::Callback;
using Microsoft::WRL::ComPtr;

namespace {
constexpr UINT NavigateMessage = WM_APP + 1;
constexpr UINT CaptureMessage = WM_APP + 2;
constexpr UINT CaptureTimer = 1;
HWND window = nullptr;
ComPtr<ICoreWebView2Controller> controller;
ComPtr<ICoreWebView2> browser;
std::wstring targetUrl;
std::filesystem::path profilePath;
HANDLE browserProcess = nullptr;
bool captureRequested = false;
bool capturePending = false;
bool completed = false;
int exitCode = 2;

std::wstring TakeString(PWSTR value) {
    std::wstring result = value ? value : L"";
    CoTaskMemFree(value);
    return result;
}

std::string Quote(const std::wstring& text) {
    int size = WideCharToMultiByte(CP_UTF8, 0, text.data(),
        static_cast<int>(text.size()), nullptr, 0, nullptr, nullptr);
    std::string utf8(size, '\0');
    WideCharToMultiByte(CP_UTF8, 0, text.data(), static_cast<int>(text.size()),
        utf8.data(), size, nullptr, nullptr);
    std::string result = "\"";
    for (unsigned char character : utf8) {
        switch (character) {
        case '"': result += "\\\""; break;
        case '\\': result += "\\\\"; break;
        default:
            if (character < 0x20) {
                const char* digits = "0123456789abcdef";
                result += "\\u00";
                result += digits[character >> 4];
                result += digits[character & 15];
            } else {
                result += static_cast<char>(character);
            }
        }
    }
    return result + "\"";
}

void Finish(const std::string& payload, int result) {
    if (completed) return;
    completed = true;
    exitCode = result;
    std::string message = payload + "\n";
    DWORD written = 0;
    WriteFile(GetStdHandle(STD_OUTPUT_HANDLE), message.data(),
        static_cast<DWORD>(message.size()), &written, nullptr);
    PostMessageW(window, WM_CLOSE, 0, 0);
}

void Fail(const char* category) {
    Finish(std::string("{\"error\":\"") + category + "\"}", 1);
}

void CaptureCookies() {
    if (!captureRequested || capturePending || !browser || completed) return;
    ComPtr<ICoreWebView2_2> browser2;
    ComPtr<ICoreWebView2CookieManager> manager;
    if (FAILED(browser.As(&browser2)) ||
        FAILED(browser2->get_CookieManager(&manager))) {
        Fail("cookie_failed");
        return;
    }
    capturePending = true;
    HRESULT request = manager->GetCookies(nullptr,
        Callback<ICoreWebView2GetCookiesCompletedHandler>(
            [](HRESULT status, ICoreWebView2CookieList* cookies) -> HRESULT {
                capturePending = false;
                if (completed) return S_OK;
                if (FAILED(status) || !cookies) {
                    Fail("cookie_failed");
                    return S_OK;
                }
                UINT count = 0;
                cookies->get_Count(&count);
                std::string serialized;
                bool authenticated = false;
                for (UINT index = 0; index < count; ++index) {
                    ComPtr<ICoreWebView2Cookie> cookie;
                    if (FAILED(cookies->GetValueAtIndex(index, &cookie))) continue;
                    PWSTR nameRaw = nullptr, valueRaw = nullptr;
                    PWSTR domainRaw = nullptr, pathRaw = nullptr;
                    cookie->get_Name(&nameRaw);
                    cookie->get_Value(&valueRaw);
                    cookie->get_Domain(&domainRaw);
                    cookie->get_Path(&pathRaw);
                    std::wstring name = TakeString(nameRaw);
                    std::wstring value = TakeString(valueRaw);
                    std::wstring domain = TakeString(domainRaw);
                    std::wstring path = TakeString(pathRaw);
                    if (domain != L".nexusmods.com" && domain != L"www.nexusmods.com")
                        continue;
                    BOOL secure = FALSE, httpOnly = FALSE, session = FALSE;
                    double expires = 0;
                    cookie->get_IsSecure(&secure);
                    cookie->get_IsHttpOnly(&httpOnly);
                    cookie->get_IsSession(&session);
                    cookie->get_Expires(&expires);
                    if (!session && expires <= static_cast<double>(std::time(nullptr)))
                        continue;
                    if (name == L"nexusmods_session" && !value.empty())
                        authenticated = true;
                    std::wstring header = name + L"=" + value + L"; Domain=" + domain
                        + L"; Path=" + (path.empty() ? L"/" : path);
                    if (secure) header += L"; Secure";
                    if (httpOnly) header += L"; HttpOnly";
                    if (!session) {
                        std::time_t timestamp = static_cast<std::time_t>(expires);
                        std::tm utc{};
                        char date[64]{};
                        if (gmtime_s(&utc, &timestamp) == 0) {
                            std::strftime(date, sizeof(date),
                                "%a, %d %b %Y %H:%M:%S GMT", &utc);
                            header += L"; Expires=";
                            header.append(date, date + std::char_traits<char>::length(date));
                        }
                    }
                    if (!serialized.empty()) serialized += ",";
                    serialized += Quote(header);
                }
                if (!authenticated) return S_OK;
                ComPtr<ICoreWebView2Settings> settings;
                ComPtr<ICoreWebView2Settings2> settings2;
                PWSTR userAgent = nullptr;
                if (FAILED(browser->get_Settings(&settings)) ||
                    FAILED(settings.As(&settings2)) ||
                    FAILED(settings2->get_UserAgent(&userAgent))) {
                    Fail("cookie_failed");
                    return S_OK;
                }
                Finish("{\"user_agent\":" + Quote(TakeString(userAgent))
                    + ",\"cookies\":[" + serialized + "]}", 0);
                return S_OK;
            }).Get());
    if (FAILED(request)) {
        capturePending = false;
        Fail("cookie_failed");
    }
}

DWORD WINAPI ReadCommands(void*) {
    std::string line;
    char character;
    DWORD read = 0;
    bool first = true;
    while (ReadFile(GetStdHandle(STD_INPUT_HANDLE), &character, 1, &read, nullptr)
        && read == 1) {
        if (character == '\r') continue;
        if (character != '\n') {
            if (line.size() >= 16384) break;
            line += character;
            continue;
        }
        if (first) {
            first = false;
            int length = MultiByteToWideChar(CP_UTF8, MB_ERR_INVALID_CHARS,
                line.data(), static_cast<int>(line.size()), nullptr, 0);
            auto url = new std::wstring(length, L'\0');
            MultiByteToWideChar(CP_UTF8, MB_ERR_INVALID_CHARS, line.data(),
                static_cast<int>(line.size()), url->data(), length);
            if (!PostMessageW(window, NavigateMessage, 0,
                reinterpret_cast<LPARAM>(url))) delete url;
        } else if (line == "capture") {
            PostMessageW(window, CaptureMessage, 0, 0);
        } else {
            break;
        }
        line.clear();
    }
    // Closing the parent's pipe also closes the browser, including after parent exit.
    PostMessageW(window, WM_CLOSE, 0, 0);
    return 0;
}

LRESULT CALLBACK WindowProcedure(HWND handle, UINT message, WPARAM wparam,
    LPARAM lparam) {
    switch (message) {
    case NavigateMessage: {
        auto url = reinterpret_cast<std::wstring*>(lparam);
        targetUrl = *url;
        delete url;
        if (targetUrl.rfind(L"https://www.nexusmods.com/sso?", 0) != 0) {
            Fail("invalid_request");
        } else if (browser) {
            browser->Navigate(targetUrl.c_str());
        }
        return 0;
    }
    case CaptureMessage:
        captureRequested = true;
        SetTimer(handle, CaptureTimer, 500, nullptr);
        CaptureCookies();
        return 0;
    case WM_TIMER:
        if (wparam == CaptureTimer) CaptureCookies();
        return 0;
    case WM_SIZE:
        if (controller) {
            RECT bounds;
            GetClientRect(handle, &bounds);
            controller->put_Bounds(bounds);
        }
        return 0;
    case WM_DESTROY:
        completed = true;
        KillTimer(handle, CaptureTimer);
        if (browser) {
            UINT32 processId = 0;
            browser->get_BrowserProcessId(&processId);
            browserProcess = OpenProcess(SYNCHRONIZE, FALSE, processId);
        }
        if (controller) controller->Close();
        PostQuitMessage(0);
        return 0;
    }
    return DefWindowProcW(handle, message, wparam, lparam);
}
}

int WINAPI wWinMain(HINSTANCE instance, HINSTANCE, PWSTR, int) {
    if (FAILED(CoInitializeEx(nullptr, COINIT_APARTMENTTHREADED))) return 1;
    SetProcessDPIAware();
    WNDCLASSW windowClass{};
    windowClass.lpfnWndProc = WindowProcedure;
    windowClass.hInstance = instance;
    windowClass.lpszClassName = L"SSEATWebView2Login";
    windowClass.hCursor = LoadCursor(nullptr, IDC_ARROW);
    windowClass.hIcon = LoadIconW(instance, MAKEINTRESOURCEW(1));
    RegisterClassW(&windowClass);
    window = CreateWindowW(windowClass.lpszClassName, L"Nexus Mods login - SSE-AT",
        WS_OVERLAPPEDWINDOW, CW_USEDEFAULT, CW_USEDEFAULT, 1100, 850,
        nullptr, nullptr, instance, nullptr);
    if (!window) return 1;

    int argumentCount = 0;
    LPWSTR* arguments = CommandLineToArgvW(GetCommandLineW(), &argumentCount);
    if (arguments && argumentCount == 5 &&
        std::wstring(arguments[1]) == L"--window-theme") {
        const DWORD attributes[] = {20, 35, 36};
        for (int index = 0; index < 3; ++index) {
            wchar_t* end = nullptr;
            DWORD value = std::wcstoul(arguments[index + 2], &end, 10);
            if (end != arguments[index + 2] && *end == L'\0') {
                DwmSetWindowAttribute(window, attributes[index], &value, sizeof(value));
            }
        }
    }
    LocalFree(arguments);

    wchar_t executable[32768];
    GetModuleFileNameW(nullptr, executable, 32768);
    auto loaderPath = std::filesystem::path(executable).parent_path()
        / L"WebView2Loader.dll";
    HMODULE loader = LoadLibraryExW(loaderPath.c_str(), nullptr,
        LOAD_LIBRARY_SEARCH_DLL_LOAD_DIR | LOAD_LIBRARY_SEARCH_DEFAULT_DIRS);
    using GetVersion = HRESULT(STDMETHODCALLTYPE*)(PCWSTR, LPWSTR*);
    using CreateEnvironment = HRESULT(STDMETHODCALLTYPE*)(PCWSTR, PCWSTR,
        ICoreWebView2EnvironmentOptions*,
        ICoreWebView2CreateCoreWebView2EnvironmentCompletedHandler*);
    auto getVersion = loader ? reinterpret_cast<GetVersion>(
        GetProcAddress(loader, "GetAvailableCoreWebView2BrowserVersionString")) : nullptr;
    auto createEnvironment = loader ? reinterpret_cast<CreateEnvironment>(
        GetProcAddress(loader, "CreateCoreWebView2EnvironmentWithOptions")) : nullptr;
    PWSTR runtimeVersion = nullptr;
    if (!getVersion || !createEnvironment || FAILED(getVersion(nullptr, &runtimeVersion))) {
        CoTaskMemFree(runtimeVersion);
        Fail("runtime_missing");
    } else {
        CoTaskMemFree(runtimeVersion);
        GUID identifier;
        CoCreateGuid(&identifier);
        wchar_t identifierText[40];
        StringFromGUID2(identifier, identifierText, 40);
        profilePath = std::filesystem::temp_directory_path()
            / (std::wstring(L"SSE-AT-WebView2-") + identifierText);
        HRESULT result = createEnvironment(nullptr, profilePath.c_str(), nullptr,
            Callback<ICoreWebView2CreateCoreWebView2EnvironmentCompletedHandler>(
                [](HRESULT status, ICoreWebView2Environment* environment) -> HRESULT {
                    if (completed) return S_OK;
                    ComPtr<ICoreWebView2Environment10> environment10;
                    ComPtr<ICoreWebView2ControllerOptions> options;
                    if (FAILED(status) || !environment ||
                        FAILED(environment->QueryInterface(IID_PPV_ARGS(&environment10))) ||
                        FAILED(environment10->CreateCoreWebView2ControllerOptions(&options))) {
                        Fail("initialization_failed");
                        return S_OK;
                    }
                    if (FAILED(options->put_IsInPrivateModeEnabled(TRUE))) {
                        Fail("initialization_failed");
                        return S_OK;
                    }
                    HRESULT result = environment10->CreateCoreWebView2ControllerWithOptions(
                        window, options.Get(),
                        Callback<ICoreWebView2CreateCoreWebView2ControllerCompletedHandler>(
                            [](HRESULT status, ICoreWebView2Controller* created) -> HRESULT {
                                if (completed) return S_OK;
                                if (FAILED(status) || !created) {
                                    Fail("initialization_failed");
                                    return S_OK;
                                }
                                controller = created;
                                if (FAILED(controller->get_CoreWebView2(&browser))) {
                                    Fail("initialization_failed");
                                    return S_OK;
                                }
                                RECT bounds;
                                GetClientRect(window, &bounds);
                                controller->put_Bounds(bounds);
                                if (!targetUrl.empty()) browser->Navigate(targetUrl.c_str());
                                ShowWindow(window, SW_SHOW);
                                controller->put_IsVisible(TRUE);
                                SetForegroundWindow(window);
                                return S_OK;
                            }).Get());
                    if (FAILED(result)) Fail("initialization_failed");
                    return S_OK;
                }).Get());
        if (FAILED(result)) Fail("initialization_failed");
        HANDLE reader = CreateThread(nullptr, 0, ReadCommands, nullptr, 0, nullptr);
        if (reader) CloseHandle(reader);
        else Fail("initialization_failed");
    }
    MSG message;
    while (GetMessageW(&message, nullptr, 0, 0) > 0) {
        TranslateMessage(&message);
        DispatchMessageW(&message);
    }
    browser.Reset();
    controller.Reset();
    CoUninitialize();
    // Only remove our unique temporary profile after its browser process exits.
    bool stopped = !browserProcess ||
        WaitForSingleObject(browserProcess, 2500) == WAIT_OBJECT_0;
    if (browserProcess) CloseHandle(browserProcess);
    if (stopped && !profilePath.empty() &&
        profilePath.parent_path() == std::filesystem::temp_directory_path() &&
        profilePath.filename().wstring().rfind(L"SSE-AT-WebView2-{", 0) == 0) {
        std::error_code ignored;
        std::filesystem::remove_all(profilePath, ignored);
    }
    return exitCode;
}
