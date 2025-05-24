from google.cloud import texttospeech
import os
from app import app, db, Card
import uuid

def generate_audio_for_card(card):
    """Generate audio file for a card using Google Cloud TTS, using the front_language field."""
    try:
        # Initialize the client
        client = texttospeech.TextToSpeechClient()

        # Use the language specified in the card, default to 'ja'
        tts_language = card.front_language or 'ja'
        # Only use the Japanese part for audio (before the first line break)
        tts_text = card.front.split('\n')[0].replace('_', '　')

        # Set the language code for Google TTS
        if tts_language == 'ja':
            language_code = 'ja-JP'
            voice_name = 'ja-JP-Chirp3-HD-Kore'
            gender = texttospeech.SsmlVoiceGender.FEMALE
        elif tts_language == 'en':
            language_code = 'en-US'
            voice_name = 'en-US-Wavenet-F'
            gender = texttospeech.SsmlVoiceGender.FEMALE
        else:
            language_code = f'{tts_language}-JP'
            voice_name = None
            gender = texttospeech.SsmlVoiceGender.NEUTRAL

        # Build the voice request
        voice = texttospeech.VoiceSelectionParams(
            language_code=language_code,
            name=voice_name,
            ssml_gender=gender
        )

        # Set the text input to be synthesized
        synthesis_input = texttospeech.SynthesisInput(text=tts_text)

        # Select the type of audio file
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3
        )

        # Perform the text-to-speech request
        response = client.synthesize_speech(
            input=synthesis_input, voice=voice, audio_config=audio_config
        )

        # Create audio directory if it doesn't exist
        audio_dir = os.path.join(app.static_folder, 'audio')
        if not os.path.exists(audio_dir):
            os.makedirs(audio_dir)

        # Generate unique filename
        filename = f"{uuid.uuid4()}.mp3"
        filepath = os.path.join(audio_dir, filename)

        # Write the response to the output file
        with open(filepath, "wb") as out:
            out.write(response.audio_content)

        # Update card with audio path
        card.audio_path = f"/static/audio/{filename}"
        db.session.commit()

        print(f"Generated audio for card {card.id}")
        return True

    except Exception as e:
        print(f"Error generating audio for card {card.id}: {str(e)}")
        return False

def generate_all_audio():
    """Generate audio for all cards that don't have it yet."""
    with app.app_context():
        cards = Card.query.filter_by(audio_path=None).all()
        for card in cards:
            generate_audio_for_card(card)

if __name__ == '__main__':
    generate_all_audio()

with app.app_context():
    for ex in Card.query.all():
        print(ex.id, ex.audio_path) 