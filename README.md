
# Project Structure

This section describes the purpose of each folder in the project:

## Core Configuration
- **agent.json** - Main agent configuration file defining the Dialogflow agent settings, speech-to-text settings, and default flow.

## emotion/
Contains emotion-related animations and demonstrations for the NAO robot:
- `eye_pulse_animator.py` - Reusable helper class for driving NAO's eye LEDs through color pulses to express emotions
- `led_emotion_demo.py` - Demo script showcasing LED-based emotion expressions

## flows/
Contains Dialogflow conversation flow definitions:
- **Default Start Flow/** - Initial conversation flow with transition route groups for Agent, Appraisal, Confirmation, Dialog, Emotions, Greetings, and User interactions
- **Fairytale story/** - Flow for fairytale storytelling interactions with pages for acknowledgement logic, engine hub, interaction, performance, and story kickoff
- **SIR_flow/** - Main SIR project flow with pages for cycle setup, data collection, narrative generation, performance output, and session end

## generativeSettings/
Contains language-specific settings for generative responses (e.g., `en.json` for English).

## generators/
Contains generator configurations for various content generation tasks. Each generator folder includes:
- Generator configuration JSON file
- Language-specific phrase files (e.g., `phrases/en.json`)

Generators include:
- Animation generation
- Confirmation generation
- Introduction generation
- Name animation and reaction
- Prompt generation
- Question generation
- Story generation and story segments
- Narrative orchestration and weaving
- Story kickoff generation

## gesture_names.txt
List of gesture/animation file paths available on the NAO robot for body language and movement animations.

## intents/
Contains Dialogflow intent definitions (188 JSON files) that define how the agent recognizes and responds to user inputs.

## playbooks/
Contains playbook configurations for structured interaction scenarios:
- **Fairytale-playbook/** - Playbook for fairytale storytelling interactions

## speech-audio/
Contains scripts for speech and audio processing:
- `demo_theatrical_preformance.py` - Demo script for theatrical performance with audio playback
- `test_background+nao.py` - Testing script for background audio with NAO integration
- `test_whisper_audio` - Audio testing script using Whisper

## testCases/
Contains test case definitions (40 JSON files) covering:
- Happy path scenarios (greetings, jokes, conversations, user interactions)
- Error handling scenarios (unexpected inputs, out-of-scope requests)

