"""Keep the previous recording URL as a route into the concept page."""
from reference_audio import write_legacy

def render():
    write_legacy('explained')

if __name__=='__main__':render()
