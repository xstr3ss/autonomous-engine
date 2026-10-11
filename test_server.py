from server import start_server

def test_start_server():
    assert start_server() == "Connected to Enterprise DB!"
