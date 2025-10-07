#!/usr/bin/env python3
"""
Test script for PDF Reader MCP Server
"""
import asyncio
import sys
import os
sys.path.insert(0, 'src')

from academic_pdf_reader_mcp.server import PDFProcessor, handle_call_tool, handle_list_tools, handle_get_prompt

async def test_all_functions():
    pdf_path = 'data/Rosenblatt1958.pdf'
    
    print("🔍 Testing PDF Reader MCP Server")
    print("=" * 50)
    
    # Test 1: Metadata
    print("\n📋 Test 1: Metadata Extraction")
    try:
        metadata = await PDFProcessor.get_metadata(pdf_path)
        print(f"✅ Title: {metadata.get('title', 'N/A')}")
        print(f"✅ Author: {metadata.get('author', 'N/A')}")
        print(f"✅ Pages: {metadata['page_count']}")
        print(f"✅ File Size: {metadata['file_size']:,} bytes")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: Text Extraction
    print("\n📝 Test 2: Text Extraction")
    try:
        text = await PDFProcessor.extract_text(pdf_path, 0)
        print(f"✅ First page text ({len(text)} chars): {text[:100]}...")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 3: Image Extraction  
    print("\n🖼️ Test 3: Image Extraction")
    try:
        images = await PDFProcessor.extract_images(pdf_path)
        print(f"✅ Found {len(images)} images")
        for i, img in enumerate(images[:2]):
            print(f"   Image {i+1}: {img['width']}x{img['height']} on page {img['page']}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 4: Page Rendering
    print("\n🎨 Test 4: Page Rendering")
    try:
        img_data = await PDFProcessor.render_page(pdf_path, 0, 72)
        print(f"✅ Rendered page to {len(img_data)} bytes of base64 PNG")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 5: Tools List
    print("\n🛠️ Test 5: MCP Tools")
    try:
        tools = await handle_list_tools()
        print(f"✅ Available tools: {len(tools)}")
        for tool in tools:
            print(f"   - {tool.name}: {tool.description}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 6: Tool Execution
    print("\n⚡ Test 6: Tool Execution")
    try:
        # Mock server context for testing
        class MockSession:
            async def send_resource_list_changed(self):
                pass
        
        class MockContext:
            def __init__(self):
                self.session = MockSession()
        
        # Import the server module to set the request context
        from academic_pdf_reader_mcp import server
        server.server.request_context = MockContext()
        
        result = await handle_call_tool("get-metadata", {"file_path": pdf_path})
        print(f"✅ Tool execution successful: {len(result)} content items returned")
        print(f"   Result preview: {result[0].text[:100]}...")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n🎉 PDF Reader Test Complete!")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(test_all_functions())