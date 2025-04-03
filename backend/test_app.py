import pytest
from flask import Flask
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor

# Assume your Flask app is defined in app.py as 'app'
from app import app

@pytest.fixture(scope="function")
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture(scope="function")
def test_tracer():
    # Create an in-memory span exporter to capture spans
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    # Set the provider so the instrumentation uses it
    trace.set_tracer_provider(provider)
    # Instrument the Flask app with OpenTelemetry
    FlaskInstrumentor().instrument_app(app)
    yield exporter
    exporter.clear()

def test_homepage_and_tracing(client, test_tracer):
    response = client.get("/")
    assert response.status_code == 200
    # Check if a span was created for the GET request
    spans = test_tracer.get_finished_spans()
    # For example, verify that at least one span contains the route name "GET /"
    assert any("GET /" in span.name for span in spans), "Expected span for GET request not found"