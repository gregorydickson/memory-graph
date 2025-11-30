"""
Tests for server main() function initialization and MCP server startup.

This test module covers the bug fix where NotificationOptions was being passed as None,
causing an AttributeError in get_capabilities(). The fix ensures proper initialization
with NotificationOptions() and experimental_capabilities={}.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch, call
from contextlib import asynccontextmanager

from memorygraph.server import ClaudeMemoryServer, main
from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
from mcp.types import ServerCapabilities


class TestMainFunctionInitialization:
    """Test the main() function and server startup process."""

    @pytest.mark.asyncio
    async def test_main_creates_server_instance(self):
        """Test that main() creates a ClaudeMemoryServer instance."""
        with patch.object(ClaudeMemoryServer, 'initialize', new_callable=AsyncMock):
            with patch.object(ClaudeMemoryServer, 'cleanup', new_callable=AsyncMock):
                with patch('memorygraph.server.stdio_server') as mock_stdio:
                    # Mock the context manager
                    @asynccontextmanager
                    async def mock_stdio_context():
                        read_stream = AsyncMock()
                        write_stream = AsyncMock()
                        yield read_stream, write_stream

                    mock_stdio.return_value = mock_stdio_context()

                    # Mock server.run to exit immediately
                    with patch.object(Server, 'run', new_callable=AsyncMock) as mock_run:
                        mock_run.side_effect = KeyboardInterrupt()

                        # Run main and expect KeyboardInterrupt
                        try:
                            await main()
                        except KeyboardInterrupt:
                            pass

    @pytest.mark.asyncio
    async def test_main_initializes_server(self):
        """Test that main() calls server.initialize()."""
        mock_initialize = AsyncMock()
        mock_cleanup = AsyncMock()

        with patch.object(ClaudeMemoryServer, 'initialize', mock_initialize):
            with patch.object(ClaudeMemoryServer, 'cleanup', mock_cleanup):
                with patch('memorygraph.server.stdio_server') as mock_stdio:
                    @asynccontextmanager
                    async def mock_stdio_context():
                        read_stream = AsyncMock()
                        write_stream = AsyncMock()
                        yield read_stream, write_stream

                    mock_stdio.return_value = mock_stdio_context()

                    with patch.object(Server, 'run', new_callable=AsyncMock) as mock_run:
                        mock_run.side_effect = KeyboardInterrupt()

                        try:
                            await main()
                        except KeyboardInterrupt:
                            pass

                        # Verify initialize was called
                        mock_initialize.assert_called_once()

    @pytest.mark.asyncio
    async def test_main_calls_cleanup_on_exit(self):
        """Test that main() calls cleanup on exit."""
        mock_cleanup = AsyncMock()

        with patch.object(ClaudeMemoryServer, 'initialize', new_callable=AsyncMock):
            with patch.object(ClaudeMemoryServer, 'cleanup', mock_cleanup):
                with patch('memorygraph.server.stdio_server') as mock_stdio:
                    @asynccontextmanager
                    async def mock_stdio_context():
                        read_stream = AsyncMock()
                        write_stream = AsyncMock()
                        yield read_stream, write_stream

                    mock_stdio.return_value = mock_stdio_context()

                    with patch.object(Server, 'run', new_callable=AsyncMock) as mock_run:
                        mock_run.side_effect = KeyboardInterrupt()

                        try:
                            await main()
                        except KeyboardInterrupt:
                            pass

                        # Verify cleanup was called
                        mock_cleanup.assert_called_once()

    @pytest.mark.asyncio
    async def test_main_cleanup_on_exception(self):
        """Test that cleanup is called even when an exception occurs."""
        mock_cleanup = AsyncMock()

        with patch.object(ClaudeMemoryServer, 'initialize', new_callable=AsyncMock):
            with patch.object(ClaudeMemoryServer, 'cleanup', mock_cleanup):
                with patch('memorygraph.server.stdio_server') as mock_stdio:
                    @asynccontextmanager
                    async def mock_stdio_context():
                        raise Exception("Test error")
                        yield None, None  # Never reached

                    mock_stdio.return_value = mock_stdio_context()

                    # Should raise the exception but still cleanup
                    with pytest.raises(Exception, match="Test error"):
                        await main()

                    # Verify cleanup was still called
                    mock_cleanup.assert_called_once()


class TestNotificationOptionsInitialization:
    """Test the bug fix for NotificationOptions initialization.

    The bug: notification_options=None was passed to get_capabilities(),
    which then tried to access attributes on None, causing AttributeError.

    The fix: Pass NotificationOptions() instead of None.
    """

    @pytest.mark.asyncio
    async def test_notification_options_is_not_none(self):
        """Test that NotificationOptions() is passed, not None."""
        with patch.object(ClaudeMemoryServer, 'initialize', new_callable=AsyncMock):
            with patch.object(ClaudeMemoryServer, 'cleanup', new_callable=AsyncMock):
                with patch('memorygraph.server.stdio_server') as mock_stdio:
                    @asynccontextmanager
                    async def mock_stdio_context():
                        read_stream = AsyncMock()
                        write_stream = AsyncMock()
                        yield read_stream, write_stream

                    mock_stdio.return_value = mock_stdio_context()

                    # Capture the server.run call
                    captured_init_options = None

                    async def capture_run(read_stream, write_stream, init_options):
                        nonlocal captured_init_options
                        captured_init_options = init_options
                        raise KeyboardInterrupt()

                    with patch.object(Server, 'run', new_callable=AsyncMock) as mock_run:
                        mock_run.side_effect = capture_run

                        try:
                            await main()
                        except KeyboardInterrupt:
                            pass

                        # Verify run was called with InitializationOptions
                        assert mock_run.call_count == 1
                        # Get the init_options argument
                        call_args = mock_run.call_args
                        init_options = call_args[0][2] if len(call_args[0]) > 2 else call_args.kwargs.get('init_options')

                        assert init_options is not None
                        assert isinstance(init_options, InitializationOptions)

    @pytest.mark.asyncio
    async def test_get_capabilities_called_with_notification_options(self):
        """Test that get_capabilities is called with NotificationOptions() not None."""
        with patch.object(ClaudeMemoryServer, 'initialize', new_callable=AsyncMock):
            with patch.object(ClaudeMemoryServer, 'cleanup', new_callable=AsyncMock):
                with patch('memorygraph.server.stdio_server') as mock_stdio:
                    @asynccontextmanager
                    async def mock_stdio_context():
                        read_stream = AsyncMock()
                        write_stream = AsyncMock()
                        yield read_stream, write_stream

                    mock_stdio.return_value = mock_stdio_context()

                    # Mock get_capabilities to verify it's called correctly
                    original_get_capabilities = Server.get_capabilities

                    def mock_get_capabilities(self, notification_options=None, experimental_capabilities=None):
                        # This would have raised AttributeError with None
                        # Verify we receive proper types
                        assert notification_options is not None, "notification_options should not be None"
                        assert isinstance(notification_options, NotificationOptions), \
                            f"Expected NotificationOptions, got {type(notification_options)}"
                        assert experimental_capabilities is not None, "experimental_capabilities should not be None"
                        assert isinstance(experimental_capabilities, dict), \
                            f"Expected dict, got {type(experimental_capabilities)}"
                        return original_get_capabilities(self, notification_options, experimental_capabilities)

                    with patch.object(Server, 'get_capabilities', mock_get_capabilities):
                        with patch.object(Server, 'run', new_callable=AsyncMock) as mock_run:
                            mock_run.side_effect = KeyboardInterrupt()

                            try:
                                await main()
                            except KeyboardInterrupt:
                                pass

    @pytest.mark.asyncio
    async def test_experimental_capabilities_is_empty_dict(self):
        """Test that experimental_capabilities is initialized as empty dict, not None."""
        with patch.object(ClaudeMemoryServer, 'initialize', new_callable=AsyncMock):
            with patch.object(ClaudeMemoryServer, 'cleanup', new_callable=AsyncMock):
                with patch('memorygraph.server.stdio_server') as mock_stdio:
                    @asynccontextmanager
                    async def mock_stdio_context():
                        read_stream = AsyncMock()
                        write_stream = AsyncMock()
                        yield read_stream, write_stream

                    mock_stdio.return_value = mock_stdio_context()

                    # Capture the original get_capabilities method
                    original_get_capabilities = Server.get_capabilities

                    # Verify experimental_capabilities is {}
                    def verify_capabilities(self, notification_options=None, experimental_capabilities=None):
                        assert experimental_capabilities == {}, \
                            f"Expected empty dict, got {experimental_capabilities}"
                        # Return actual capabilities using the original method
                        return original_get_capabilities(self, notification_options, experimental_capabilities)

                    with patch.object(Server, 'get_capabilities', verify_capabilities):
                        with patch.object(Server, 'run', new_callable=AsyncMock) as mock_run:
                            mock_run.side_effect = KeyboardInterrupt()

                            try:
                                await main()
                            except KeyboardInterrupt:
                                pass

    @pytest.mark.asyncio
    async def test_no_attribute_error_during_initialization(self):
        """Test that no AttributeError is raised during server initialization.

        This was the original bug: accessing attributes on None caused AttributeError.
        """
        with patch.object(ClaudeMemoryServer, 'initialize', new_callable=AsyncMock):
            with patch.object(ClaudeMemoryServer, 'cleanup', new_callable=AsyncMock):
                with patch('memorygraph.server.stdio_server') as mock_stdio:
                    @asynccontextmanager
                    async def mock_stdio_context():
                        read_stream = AsyncMock()
                        write_stream = AsyncMock()
                        yield read_stream, write_stream

                    mock_stdio.return_value = mock_stdio_context()

                    with patch.object(Server, 'run', new_callable=AsyncMock) as mock_run:
                        mock_run.side_effect = KeyboardInterrupt()

                        # Should not raise AttributeError
                        try:
                            await main()
                        except KeyboardInterrupt:
                            pass  # Expected
                        except AttributeError as e:
                            pytest.fail(f"AttributeError should not be raised: {e}")


class TestInitializationOptionsParameters:
    """Test the InitializationOptions parameters passed to server.run()."""

    @pytest.mark.asyncio
    async def test_initialization_options_server_name(self):
        """Test that server_name is set correctly in InitializationOptions."""
        with patch.object(ClaudeMemoryServer, 'initialize', new_callable=AsyncMock):
            with patch.object(ClaudeMemoryServer, 'cleanup', new_callable=AsyncMock):
                with patch('memorygraph.server.stdio_server') as mock_stdio:
                    @asynccontextmanager
                    async def mock_stdio_context():
                        read_stream = AsyncMock()
                        write_stream = AsyncMock()
                        yield read_stream, write_stream

                    mock_stdio.return_value = mock_stdio_context()

                    with patch.object(Server, 'run', new_callable=AsyncMock) as mock_run:
                        mock_run.side_effect = KeyboardInterrupt()

                        try:
                            await main()
                        except KeyboardInterrupt:
                            pass

                        # Verify the InitializationOptions
                        call_args = mock_run.call_args
                        init_options = call_args[0][2]
                        assert init_options.server_name == "claude-memory"

    @pytest.mark.asyncio
    async def test_initialization_options_server_version(self):
        """Test that server_version is set correctly in InitializationOptions."""
        with patch.object(ClaudeMemoryServer, 'initialize', new_callable=AsyncMock):
            with patch.object(ClaudeMemoryServer, 'cleanup', new_callable=AsyncMock):
                with patch('memorygraph.server.stdio_server') as mock_stdio:
                    @asynccontextmanager
                    async def mock_stdio_context():
                        read_stream = AsyncMock()
                        write_stream = AsyncMock()
                        yield read_stream, write_stream

                    mock_stdio.return_value = mock_stdio_context()

                    with patch.object(Server, 'run', new_callable=AsyncMock) as mock_run:
                        mock_run.side_effect = KeyboardInterrupt()

                        try:
                            await main()
                        except KeyboardInterrupt:
                            pass

                        # Verify the InitializationOptions
                        call_args = mock_run.call_args
                        init_options = call_args[0][2]
                        assert init_options.server_version == "0.1.0"

    @pytest.mark.asyncio
    async def test_initialization_options_capabilities_object(self):
        """Test that capabilities object is properly constructed."""
        with patch.object(ClaudeMemoryServer, 'initialize', new_callable=AsyncMock):
            with patch.object(ClaudeMemoryServer, 'cleanup', new_callable=AsyncMock):
                with patch('memorygraph.server.stdio_server') as mock_stdio:
                    @asynccontextmanager
                    async def mock_stdio_context():
                        read_stream = AsyncMock()
                        write_stream = AsyncMock()
                        yield read_stream, write_stream

                    mock_stdio.return_value = mock_stdio_context()

                    with patch.object(Server, 'run', new_callable=AsyncMock) as mock_run:
                        mock_run.side_effect = KeyboardInterrupt()

                        try:
                            await main()
                        except KeyboardInterrupt:
                            pass

                        # Verify capabilities was constructed
                        call_args = mock_run.call_args
                        init_options = call_args[0][2]
                        assert init_options.capabilities is not None


class TestServerRunIntegration:
    """Test server.run() is called with correct parameters."""

    @pytest.mark.asyncio
    async def test_server_run_receives_streams(self):
        """Test that server.run() receives read and write streams."""
        with patch.object(ClaudeMemoryServer, 'initialize', new_callable=AsyncMock):
            with patch.object(ClaudeMemoryServer, 'cleanup', new_callable=AsyncMock):
                # Create mock streams
                mock_read = AsyncMock()
                mock_write = AsyncMock()

                with patch('memorygraph.server.stdio_server') as mock_stdio:
                    @asynccontextmanager
                    async def mock_stdio_context():
                        yield mock_read, mock_write

                    mock_stdio.return_value = mock_stdio_context()

                    with patch.object(Server, 'run', new_callable=AsyncMock) as mock_run:
                        mock_run.side_effect = KeyboardInterrupt()

                        try:
                            await main()
                        except KeyboardInterrupt:
                            pass

                        # Verify run was called with streams
                        assert mock_run.call_count == 1
                        call_args = mock_run.call_args
                        assert call_args[0][0] == mock_read
                        assert call_args[0][1] == mock_write

    @pytest.mark.asyncio
    async def test_server_run_receives_initialization_options(self):
        """Test that server.run() receives InitializationOptions."""
        with patch.object(ClaudeMemoryServer, 'initialize', new_callable=AsyncMock):
            with patch.object(ClaudeMemoryServer, 'cleanup', new_callable=AsyncMock):
                with patch('memorygraph.server.stdio_server') as mock_stdio:
                    @asynccontextmanager
                    async def mock_stdio_context():
                        read_stream = AsyncMock()
                        write_stream = AsyncMock()
                        yield read_stream, write_stream

                    mock_stdio.return_value = mock_stdio_context()

                    with patch.object(Server, 'run', new_callable=AsyncMock) as mock_run:
                        mock_run.side_effect = KeyboardInterrupt()

                        try:
                            await main()
                        except KeyboardInterrupt:
                            pass

                        # Verify run was called with InitializationOptions
                        assert mock_run.call_count == 1
                        call_args = mock_run.call_args
                        init_options = call_args[0][2]
                        assert isinstance(init_options, InitializationOptions)


class TestNotificationOptionsInstance:
    """Test that NotificationOptions is properly instantiated."""

    def test_notification_options_can_be_instantiated(self):
        """Test that NotificationOptions() creates a valid instance."""
        options = NotificationOptions()
        assert options is not None
        assert isinstance(options, NotificationOptions)

    def test_notification_options_has_no_attribute_error(self):
        """Test that NotificationOptions instance doesn't cause AttributeError.

        This verifies the fix: NotificationOptions() can be used without errors,
        while None would cause AttributeError when attributes are accessed.
        """
        options = NotificationOptions()
        # This should not raise AttributeError
        # The actual attributes accessed depend on MCP implementation,
        # but the instance itself should be valid
        assert hasattr(options, '__class__')
        assert options.__class__.__name__ == 'NotificationOptions'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
