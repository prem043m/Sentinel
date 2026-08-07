from app.tools.application.capability import ApplicationCapabilityProvider
from app.tools.browser.capability import BrowserCapabilityProvider
from app.tools.chat.capability import ChatCapabilityProvider
from app.tools.filesystem.capability import FilesystemCapabilityProvider


def test_application_capability_provider_builds():
    provider = ApplicationCapabilityProvider()
    cap = provider.build()
    assert cap.tool_name == "application"
    assert any(intent.name == "open_application" for intent in cap.intents)


def test_filesystem_capability_provider_builds():
    provider = FilesystemCapabilityProvider()
    cap = provider.build()
    assert cap.tool_name == "filesystem"
    assert any(intent.name == "read_file" for intent in cap.intents)
    assert any(intent.name == "list_directory" for intent in cap.intents)


def test_browser_capability_provider_builds():
    provider = BrowserCapabilityProvider()
    cap = provider.build()
    assert cap.tool_name == "browser"
    assert any(intent.name == "open_url" for intent in cap.intents)
    assert any(intent.name == "search_web" for intent in cap.intents)


def test_chat_capability_provider_builds():
    provider = ChatCapabilityProvider()
    cap = provider.build()
    assert cap.tool_name == "llm"
    assert any(intent.name == "chat" for intent in cap.intents)
