"""
Chat API v1 endpoints.
"""
from flask import Blueprint, request, jsonify, Response, current_app
import json
import asyncio

from app.services.chat_service import ChatService
from app.models.api import APIResponse, StreamingResponse
from app.core.logging import get_logger


logger = get_logger(__name__)


def create_chat_blueprint() -> Blueprint:
    """Create chat API blueprint."""
    chat_bp = Blueprint('chat', __name__, url_prefix='/chat')
    
    @chat_bp.route('/completions', methods=['POST'])
    async def chat_completion():
        """Non-streaming chat completion."""
        try:
            data = request.get_json()
            message = data.get('message', '')
            use_rag = data.get('use_rag', False)
            model = data.get('model')
            provider = data.get('provider')
            
            if not message:
                response = APIResponse.error("No message provided")
                return jsonify(response.model_dump()), 400
            
            # Get or create session
            from flask import session
            if 'chat_session_id' not in session:
                chat_service = current_app.container.get(ChatService)
                session['chat_session_id'] = await chat_service.create_session()
            
            session_id = session['chat_session_id']
            
            # Get chat service
            chat_service = current_app.container.get(ChatService)
            
            # Get completion
            result = await chat_service.chat_completion(
                session_id=session_id,
                message=message,
                model=model,
                use_rag=use_rag,
                provider=provider
            )
            
            if result.success:
                response = APIResponse.success(result.data)
                return jsonify(response.model_dump())
            else:
                response = APIResponse.error(result.error or "Chat completion failed")
                return jsonify(response.model_dump()), 500
            
        except Exception as e:
            logger.error(f"Error in chat completion: {e}", exc_info=True)
            response = APIResponse.error(str(e))
            return jsonify(response.model_dump()), 500
    
    @chat_bp.route('/stream', methods=['POST'])
    async def chat_stream():
        """Streaming chat completion."""
        try:
            data = request.get_json()
            message = data.get('query', '')
            use_rag = data.get('use_rag', False)
            model = data.get('model', 'llama-3.3-70b-versatile')
            
            if not message:
                response = APIResponse.error("No message provided")
                return jsonify(response.model_dump()), 400
            
            def generate():
                """Generate streaming response."""
                try:
                    # TODO: Implement actual streaming
                    test_response = f"Echo: {message} (streaming response)"
                    
                    for char in test_response:
                        event = StreamingResponse(
                            event='message',
                            data={'text': char}
                        )
                        yield event.to_sse()
                    
                    # Send completion event
                    event = StreamingResponse(
                        event='done',
                        data={'text': ''}
                    )
                    yield event.to_sse()
                    
                except Exception as e:
                    logger.error(f"Error in stream generation: {e}")
                    error_event = StreamingResponse(
                        event='error',
                        data={'error': str(e)}
                    )
                    yield error_event.to_sse()
            
            return Response(generate(), mimetype='text/event-stream')
            
        except Exception as e:
            logger.error(f"Error in chat stream: {e}", exc_info=True)
            response = APIResponse.error(str(e))
            return jsonify(response.model_dump()), 500
    
    @chat_bp.route('/history', methods=['GET'])
    async def get_chat_history():
        """Get chat history for current session."""
        try:
            # TODO: Implement chat history retrieval
            response = APIResponse.success(
                {'history': []},
                message="Chat history implementation coming soon"
            )
            return jsonify(response.model_dump())
            
        except Exception as e:
            logger.error(f"Error getting chat history: {e}", exc_info=True)
            response = APIResponse.error(str(e))
            return jsonify(response.model_dump()), 500
    
    @chat_bp.route('/history', methods=['DELETE'])
    async def clear_chat_history():
        """Clear chat history for current session."""
        try:
            # TODO: Implement chat history clearing
            response = APIResponse.success(
                None,
                message="Chat history cleared"
            )
            return jsonify(response.model_dump())
            
        except Exception as e:
            logger.error(f"Error clearing chat history: {e}", exc_info=True)
            response = APIResponse.error(str(e))
            return jsonify(response.model_dump()), 500
    
    return chat_bp