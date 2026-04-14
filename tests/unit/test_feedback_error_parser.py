import pytest

from src.execution.feedback.error_parser import ErrorParser, ParsedError, ErrorCategory, ErrorSeverity


class TestErrorParser:

    @pytest.fixture
    def parser(self):
        return ErrorParser()

    def test_parse_import_error(self, parser):
        output = "ImportError: No module named 'foo'"
        errors = parser.parse(output, "pytest")
        assert len(errors) >= 1
        assert errors[0].category == ErrorCategory.IMPORT

    def test_parse_syntax_error(self, parser):
        output = 'SyntaxError: invalid syntax'
        errors = parser.parse(output, "pytest")
        assert len(errors) >= 1
        assert errors[0].category == ErrorCategory.SYNTAX

    def test_parse_type_error(self, parser):
        output = "TypeError: unsupported operand type(s)"
        errors = parser.parse(output, "pytest")
        assert len(errors) >= 1
        assert errors[0].category == ErrorCategory.TYPE

    def test_parse_assertion_error(self, parser):
        output = "AssertionError: expected 5 but got 3"
        errors = parser.parse(output, "pytest")
        assert len(errors) >= 1
        assert errors[0].category in (ErrorCategory.LOGIC, ErrorCategory.TEST_FAILURE)

    def test_parse_empty_output(self, parser):
        errors = parser.parse("", "pytest")
        assert len(errors) == 0

    def test_parse_no_errors(self, parser):
        output = "All tests passed!"
        errors = parser.parse(output, "pytest")
        assert len(errors) == 0

    def test_parse_multiple_errors(self, parser):
        output = """
        ImportError: No module named 'foo'
        TypeError: unsupported operand type(s)
        SyntaxError: invalid syntax
        """
        errors = parser.parse(output, "pytest")
        assert len(errors) >= 2


class TestParsedError:

    def test_creation(self):
        error = ParsedError(
            category=ErrorCategory.IMPORT,
            severity=ErrorSeverity.ERROR,
            message="No module named 'foo'",
            file_path="test.py",
            line_number=10,
        )
        assert error.message == "No module named 'foo'"
        assert error.file_path == "test.py"
        assert error.line_number == 10
        assert error.category == ErrorCategory.IMPORT
        assert error.severity == ErrorSeverity.ERROR


class TestErrorCategory:

    def test_categories_exist(self):
        assert ErrorCategory.SYNTAX
        assert ErrorCategory.IMPORT
        assert ErrorCategory.TYPE
        assert ErrorCategory.LOGIC
        assert ErrorCategory.RUNTIME
        assert ErrorCategory.TEST_FAILURE


class TestErrorSeverity:

    def test_severities_exist(self):
        assert ErrorSeverity.CRITICAL
        assert ErrorSeverity.ERROR
        assert ErrorSeverity.WARNING
        assert ErrorSeverity.INFO
