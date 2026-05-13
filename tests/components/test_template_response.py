import pytest

from dk_unicorn.components.template_response import (
    is_html_well_formed,
    get_root_element,
    assert_has_single_wrapper_element,
    element_to_str,
)
from dk_unicorn.errors import (
    MissingComponentElementError,
    MissingComponentViewElementError,
    MultipleRootComponentElementError,
    NoRootComponentElementError,
)


def test_is_html_well_formed_simple():
    assert is_html_well_formed("<div><span>text</span></div>") is True


def test_is_html_well_formed_nested():
    assert is_html_well_formed("<div><p><span>text</span></p></div>") is True


def test_is_html_well_formed_unbalanced():
    assert is_html_well_formed("<div><span>text</div>") is False


def test_is_html_well_formed_void_elements():
    assert is_html_well_formed("<div><br><input></div>") is True


def test_is_html_well_formed_empty_string():
    assert is_html_well_formed("") is True


def test_is_html_well_formed_self_closing():
    assert is_html_well_formed("<div><img></div>") is True


def test_get_root_element_simple():
    elem = get_root_element("<div>content</div>")
    assert elem.tag == "div"


def test_get_root_element_with_text():
    elem = get_root_element("<div><span>text</span></div>")
    assert elem.tag == "div"


def test_get_root_element_skips_script():
    elem = get_root_element("<script>alert('hi')</script><div>content</div>")
    assert elem.tag == "div"


def test_get_root_element_no_elements():
    with pytest.raises(MissingComponentElementError):
        get_root_element("just plain text")


def test_get_root_element_html_document():
    html_doc = '<html><body><div unicorn:view>content</div></body></html>'
    elem = get_root_element(html_doc)
    assert "unicorn:view" in elem.attrib


def test_get_root_element_html_without_view():
    html_doc = '<html><body><div>content</div></body></html>'
    with pytest.raises(MissingComponentViewElementError):
        get_root_element(html_doc)


def test_assert_single_wrapper_valid():
    assert_has_single_wrapper_element("<div>content</div>", "test")


def test_assert_single_wrapper_multiple():
    with pytest.raises(MultipleRootComponentElementError):
        assert_has_single_wrapper_element("<div>one</div><div>two</div>", "test")


def test_assert_single_wrapper_void_element():
    with pytest.raises(NoRootComponentElementError):
        assert_has_single_wrapper_element("<br>", "test")


def test_assert_single_wrapper_no_elements():
    with pytest.raises(NoRootComponentElementError):
        assert_has_single_wrapper_element("", "test")


def test_assert_single_wrapper_with_view():
    assert_has_single_wrapper_element('<div unicorn:view>content</div>', "test")


def test_element_to_str():
    from lxml import html
    elem = html.fromstring("<div>hello</div>")
    result = element_to_str(elem)
    assert "div" in result
    assert "hello" in result
