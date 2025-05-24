from google.cloud import texttospeech

client = texttospeech.TextToSpeechClient()
response = client.list_voices(language_code="ja-JP")
for voice in response.voices:
    print(f"Name: {voice.name}, Gender: {texttospeech.SsmlVoiceGender(voice.ssml_gender).name}") 