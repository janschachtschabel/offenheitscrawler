#!/usr/bin/env python3
"""
Test script for LLM integration in Offenheitscrawler.
"""

import os
import asyncio
from src.llm.llm_client import LLMClient, LLMConfig


async def test_llm_integration():
    """Test the LLM integration functionality."""
    print("🧪 Testing LLM Integration for Offenheitscrawler")
    print("=" * 50)
    
    # Check for API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ No OPENAI_API_KEY environment variable found.")
        print("💡 Please set your OpenAI API key:")
        print("   export OPENAI_API_KEY='your-api-key-here'")
        return
    
    print(f"✅ Found API key: {api_key[:8]}...")
    
    # Create LLM client
    config = LLMConfig(
        api_key=api_key,
        model="gpt-4o-mini",
        temperature=0.3,
        max_tokens=2048
    )
    
    client = LLMClient(config)
    print(f"🤖 Created LLM client with model: {config.model}")
    
    # Test connection
    print("\n🔗 Testing connection...")
    try:
        success = await client.test_connection()
        if success:
            print("✅ Connection successful!")
        else:
            print("❌ Connection failed!")
            return
    except Exception as e:
        print(f"❌ Connection error: {str(e)}")
        return
    
    # Test content analysis
    print("\n📝 Testing content analysis...")
    
    sample_content = """
    Unsere Universität ist stolz darauf, Transparenz und Offenheit zu fördern. 
    Wir veröffentlichen regelmäßig unsere Forschungsergebnisse und stellen 
    Open Access Publikationen zur Verfügung. Unsere Bibliothek bietet freien 
    Zugang zu wissenschaftlichen Ressourcen. Darüber hinaus engagieren wir uns 
    für Open Science Initiativen und unterstützen die Prinzipien von Open Data.
    """
    
    criterion_name = "Open Access Publikationen"
    criterion_description = "Die Organisation stellt wissenschaftliche Publikationen frei zugänglich zur Verfügung"
    patterns = ["open access", "freier zugang", "open science", "publikationen"]
    
    try:
        analysis = await client.analyze_content_for_criteria(
            content=sample_content,
            criterion_name=criterion_name,
            criterion_description=criterion_description,
            patterns=patterns
        )
        
        print(f"📊 Analysis Results:")
        print(f"   Fulfilled: {analysis.get('fulfilled', False)}")
        print(f"   Confidence: {analysis.get('confidence', 0.0):.2f}")
        print(f"   Justification: {analysis.get('justification', 'N/A')}")
        print(f"   Evidence: {analysis.get('evidence', [])}")
        print(f"   Found Patterns: {analysis.get('found_patterns', [])}")
        
    except Exception as e:
        print(f"❌ Content analysis failed: {str(e)}")
        return
    
    # Test enhanced pattern matching
    print("\n🔍 Testing enhanced pattern matching...")
    
    try:
        enhanced_result = await client.enhance_pattern_matching(
            content=sample_content,
            patterns=patterns,
            context="Universitäre Offenheit und Transparenz"
        )
        
        print(f"🎯 Enhanced Pattern Results:")
        print(f"   Matches Found: {enhanced_result.get('matches_found', False)}")
        print(f"   Confidence: {enhanced_result.get('confidence', 0.0):.2f}")
        print(f"   Semantic Matches: {enhanced_result.get('semantic_matches', [])}")
        print(f"   Explanation: {enhanced_result.get('explanation', 'N/A')}")
        
    except Exception as e:
        print(f"❌ Enhanced pattern matching failed: {str(e)}")
        return
    
    # Test summarization
    print("\n📋 Testing summarization...")
    
    sample_evaluation = {
        "organization_name": "Test Universität",
        "total_criteria": 10,
        "fulfilled_criteria": 7,
        "fulfillment_percentage": 70.0,
        "confidence_score": 0.85,
        "details": "Good performance in transparency and open access"
    }
    
    try:
        summary = await client.summarize_organization_analysis(
            organization_name="Test Universität",
            evaluation_results=sample_evaluation
        )
        
        print(f"📄 Generated Summary:")
        print(f"   {summary}")
        
    except Exception as e:
        print(f"❌ Summarization failed: {str(e)}")
        return
    
    print("\n🎉 All tests completed successfully!")
    print("✅ LLM integration is working properly.")


if __name__ == "__main__":
    asyncio.run(test_llm_integration())
