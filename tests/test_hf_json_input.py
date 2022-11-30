from sync_asr.hf_json_input import HuggingFaceJSON
import json


# https://en.wiktionary.org/wiki/File:En-au-sick_as_a_dog.ogg
# >>> input = "En-au-sick_as_a_dog.ogg"
# >>> from transformers import pipeline
# >>> model = "jonatasgrosman/wav2vec2-large-xlsr-53-english"
# >>> pipe = pipeline(model=model)
# >>> import json
# >>> json.dumps(output)
_SAMPLE = """
{
  "text": "sick as a dog",
  "chunks": [
    {
      "text": "sick",
      "timestamp": [
        0.28,
        0.46
      ]
    },
    {
      "text": "as",
      "timestamp": [
        0.52,
        0.58
      ]
    },
    {
      "text": "a",
      "timestamp": [
        0.66,
        0.68
      ]
    },
    {
      "text": "dog",
      "timestamp": [
        0.72,
        0.96
      ]
    }
  ]
}
"""


def test_huggingface_json():
    json_sample = json.loads(_SAMPLE)
    hf_json = HuggingFaceJSON(data=json_sample)
    assert len(hf_json.words) == 4