"""
This module contains a structured database of NAO animations and a detailed selection logic.
Animations are grouped by 'intent' (e.g., neutral, question, negation) and then by 'category'.
The `get_best_animation` function analyzes input text to pick the most contextually appropriate animation.
"""
import random

# Structured animations grouped by intent and category
ANIMATIONS_BY_CATEGORY = {
    "neutral": {
        "body_language": [
            "animations/Stand/BodyTalk/BodyLanguage/NAO/Right_Slow_AFF_01",
            "animations/Stand/BodyTalk/BodyLanguage/NAO/Center_Neutral_AFF_01",
            "animations/Stand/BodyTalk/BodyLanguage/NAO/Center_Neutral_AFF_09",
            "animations/Stand/BodyTalk/BodyLanguage/NAO/Left_Neutral_AFF_05",
            "animations/Stand/BodyTalk/BodyLanguage/NAO/Center_Strong_AFF_01",
            "animations/Stand/BodyTalk/BodyLanguage/NAO/Left_Neutral_AFF_02",
            "animations/Stand/BodyTalk/BodyLanguage/NAO/Left_Slow_AFF_02",
            "animations/Stand/BodyTalk/BodyLanguage/NAO/Center_Neutral_AFF_08",
            "animations/Stand/BodyTalk/BodyLanguage/NAO/Center_Neutral_AFF_02",
            "animations/Stand/BodyTalk/BodyLanguage/NAO/Center_Strong_AFF_04",
            "animations/Stand/BodyTalk/BodyLanguage/NAO/Left_Slow_AFF_03",
            "animations/Stand/BodyTalk/BodyLanguage/NAO/Center_Neutral_AFF_04",
            "animations/Stand/BodyTalk/BodyLanguage/NAO/Center_Strong_AFF_02",
            "animations/Stand/BodyTalk/BodyLanguage/NAO/Center_Slow_AFF_06",
            "animations/Stand/BodyTalk/BodyLanguage/NAO/Center_Neutral_AFF_11",
            "animations/Stand/BodyTalk/BodyLanguage/NAO/Left_Neutral_AFF_04",
            "animations/Stand/BodyTalk/BodyLanguage/NAO/Right_Strong_AFF_02",
            "animations/Stand/BodyTalk/BodyLanguage/NAO/Right_Slow_AFF_03",
            "animations/Stand/BodyTalk/BodyLanguage/NAO/Center_Neutral_AFF_13",
            "animations/Stand/BodyTalk/BodyLanguage/NAO/Center_Strong_AFF_05",
            "animations/Stand/BodyTalk/BodyLanguage/NAO/Right_Neutral_AFF_02",
            "animations/Stand/BodyTalk/BodyLanguage/NAO/Right_Neutral_AFF_04",
            "animations/Stand/BodyTalk/BodyLanguage/NAO/Left_Neutral_AFF_06",
            "animations/Stand/BodyTalk/BodyLanguage/NAO/Left_Strong_AFF_02",
            "animations/Stand/BodyTalk/BodyLanguage/NAO/Right_Neutral_AFF_06",
            "animations/Stand/BodyTalk/BodyLanguage/NAO/Right_Neutral_AFF_05",
            "animations/Stand/BodyTalk/BodyLanguage/NAO/Center_Neutral_AFF_10",
            "animations/Stand/BodyTalk/BodyLanguage/NAO/Center_Slow_AFF_02",
            "animations/Stand/BodyTalk/BodyLanguage/NAO/Center_Strong_AFF_08",
            "animations/Stand/BodyTalk/BodyLanguage/NAO/Center_Neutral_AFF_05",
            "animations/Stand/BodyTalk/BodyLanguage/NAO/Center_Slow_AFF_03",
            "animations/Stand/BodyTalk/BodyLanguage/NAO/Right_Slow_AFF_02",
            "animations/Stand/BodyTalk/BodyLanguage/NAO/Center_Strong_AFF_06",
            "animations/Stand/BodyTalk/BodyLanguage/NAO/Left_Slow_AFF_01",
            "animations/Stand/BodyTalk/BodyLanguage/NAO/Center_Neutral_AFF_06",
            "animations/Stand/BodyTalk/BodyLanguage/NAO/Center_Neutral_AFF_07",
            "animations/Stand/BodyTalk/BodyLanguage/NAO/Center_Neutral_AFF_12",
            "animations/Stand/BodyTalk/BodyLanguage/NAO/Center_Slow_AFF_01",
            "animations/Stand/BodyTalk/BodyLanguage/NAO/Center_Slow_AFF_05",
            "animations/Stand/BodyTalk/BodyLanguage/NAO/Center_Strong_AFF_07",
        ],
        "self_others": [
            "animations/Stand/Self & others/NAO/Left_Strong_SAO_03",
            "animations/Stand/Self & others/NAO/Center_Neutral_SAO_02",
            "animations/Stand/Self & others/NAO/Left_Strong_SAO_04",
            "animations/Stand/Self & others/NAO/Right_Neutral_SAO_03",
            "animations/Stand/Self & others/NAO/Right_Strong_SAO_04",
            "animations/Stand/Self & others/NAO/Left_Strong_SAO_05",
            "animations/Stand/Self & others/NAO/Center_Neutral_SAO_04",
            "animations/Stand/Self & others/NAO/Right_Neutral_SAO_06",
            "animations/Stand/Self & others/NAO/Left_Slow_SAO_02",
            "animations/Stand/Self & others/NAO/Center_Neutral_SAO_03",
            "animations/Stand/Self & others/NAO/Right_Neutral_SAO_02",
            "animations/Stand/Self & others/NAO/Right_Neutral_SAO_01",
            "animations/Stand/Self & others/NAO/Right_Strong_SAO_02",
            "animations/Stand/Self & others/NAO/Right_Strong_SAO_03",
            "animations/Stand/Self & others/NAO/Left_Strong_SAO_01",
            "animations/Stand/Self & others/NAO/Center_Strong_SAO_01",
            "animations/Stand/Self & others/NAO/Left_Neutral_SAO_01",
            "animations/Stand/Self & others/NAO/Right_Strong_SAO_05",
            "animations/Stand/Self & others/NAO/Left_Neutral_SAO_02",
            "animations/Stand/Self & others/NAO/Right_Slow_SAO_02",
            "animations/Stand/Self & others/NAO/Center_Neutral_SAO_01",
            "animations/Stand/Self & others/NAO/Left_Neutral_SAO_06",
            "animations/Stand/Self & others/NAO/Center_Strong_SAO_02",
            "animations/Stand/Self & others/NAO/Left_Strong_SAO_02",
            "animations/Stand/Self & others/NAO/Center_Neutral_SAO_05",
            "animations/Stand/Self & others/NAO/Left_Neutral_SAO_04",
            "animations/Stand/Self & others/NAO/Left_Neutral_SAO_05",
            "animations/Stand/Self & others/NAO/Left_Neutral_SAO_03",
            "animations/Stand/Self & others/NAO/Left_Slow_SAO_01",
            "animations/Stand/Self & others/NAO/Right_Slow_SAO_01",
            "animations/Stand/Self & others/NAO/Right_Neutral_SAO_04",
            "animations/Stand/Self & others/NAO/Right_Strong_SAO_01",
            "animations/Stand/Self & others/NAO/Right_Neutral_SAO_05",
        ],
        "negation": [
            "animations/Stand/Negation/NAO/Left_Strong_NEG_01",
            "animations/Stand/Negation/NAO/Left_Strong_NEG_04",
            "animations/Stand/Negation/NAO/Right_Neutral_NEG_01",
            "animations/Stand/Negation/NAO/Center_Slow_NEG_01",
            "animations/Stand/Negation/NAO/Left_Strong_NEG_03",
            "animations/Stand/Negation/NAO/Center_Neutral_NEG_03",
            "animations/Stand/Negation/NAO/Center_Strong_NEG_05",
            "animations/Stand/Negation/NAO/Right_Strong_NEG_01",
            "animations/Stand/Negation/NAO/Left_Strong_NEG_02",
            "animations/Stand/Negation/NAO/Center_Strong_NEG_01",
            "animations/Stand/Negation/NAO/Center_Neutral_NEG_01",
            "animations/Stand/Negation/NAO/Right_Strong_NEG_03",
            "animations/Stand/Negation/NAO/Left_Neutral_NEG_01",
            "animations/Stand/Negation/NAO/Center_Slow_NEG_02",
            "animations/Stand/Negation/NAO/Center_Strong_NEG_03",
            "animations/Stand/Negation/NAO/Right_Strong_NEG_02",
            "animations/Stand/Negation/NAO/Center_Neutral_NEG_04",
            "animations/Stand/Negation/NAO/Center_Strong_NEG_04",
            "animations/Stand/Negation/NAO/Center_Neutral_NEG_02",
            "animations/Stand/Negation/NAO/Right_Strong_NEG_04",
        ],
        "enumeration": [
            "animations/Stand/Enumeration/NAO/Center_Strong_ENU_03",
            "animations/Stand/Enumeration/NAO/Center_Neutral_ENU_06",
            "animations/Stand/Enumeration/NAO/Center_Slow_ENU_01",
            "animations/Stand/Enumeration/NAO/Center_Neutral_ENU_03",
            "animations/Stand/Enumeration/NAO/Center_Neutral_ENU_02",
            "animations/Stand/Enumeration/NAO/Right_Neutral_ENU_04",
            "animations/Stand/Enumeration/NAO/Center_Neutral_ENU_07",
            "animations/Stand/Enumeration/NAO/Left_Strong_ENU_03",
            "animations/Stand/Enumeration/NAO/Center_Slow_ENU_04",
            "animations/Stand/Enumeration/NAO/Left_Neutral_ENU_02",
            "animations/Stand/Enumeration/NAO/Center_Neutral_ENU_04",
            "animations/Stand/Enumeration/NAO/Center_Strong_ENU_02",
            "animations/Stand/Enumeration/NAO/Left_Strong_ENU_02",
            "animations/Stand/Enumeration/NAO/Center_Strong_ENU_01",
            "animations/Stand/Enumeration/NAO/Left_Neutral_ENU_03",
            "animations/Stand/Enumeration/NAO/Center_Slow_ENU_02",
            "animations/Stand/Enumeration/NAO/Right_Neutral_ENU_05",
            "animations/Stand/Enumeration/NAO/Right_Neutral_ENU_03",
            "animations/Stand/Enumeration/NAO/Left_Neutral_ENU_04",
            "animations/Stand/Enumeration/NAO/Left_Neutral_ENU_01",
            "animations/Stand/Enumeration/NAO/Center_Slow_ENU_03",
            "animations/Stand/Enumeration/NAO/Left_Strong_ENU_04",
            "animations/Stand/Enumeration/NAO/Right_Neutral_ENU_01",
            "animations/Stand/Enumeration/NAO/Right_Strong_ENU_04",
            "animations/Stand/Enumeration/NAO/Center_Neutral_ENU_01",
            "animations/Stand/Enumeration/NAO/Right_Strong_ENU_03",
            "animations/Stand/Enumeration/NAO/Right_Strong_ENU_02",
            "animations/Stand/Enumeration/NAO/Left_Neutral_ENU_05",
            "animations/Stand/Enumeration/NAO/Right_Neutral_ENU_02",
        ],
        "question": [
            "animations/Stand/Question/NAO/Right_Neutral_QUE_03",
            "animations/Stand/Question/NAO/Center_Neutral_QUE_01",
            "animations/Stand/Question/NAO/Center_Slow_QUE_03",
            "animations/Stand/Question/NAO/Center_Neutral_QUE_09",
            "animations/Stand/Question/NAO/Center_Neutral_QUE_05",
            "animations/Stand/Question/NAO/Center_Neutral_QUE_08",
            "animations/Stand/Question/NAO/Center_Slow_QUE_02",
            "animations/Stand/Question/NAO/Center_Neutral_QUE_10",
            "animations/Stand/Question/NAO/Center_Strong_QUE_03",
            "animations/Stand/Question/NAO/Left_Neutral_QUE_02",
            "animations/Stand/Question/NAO/Center_Slow_QUE_01",
            "animations/Stand/Question/NAO/Center_Strong_QUE_02",
            "animations/Stand/Question/NAO/Center_Neutral_QUE_04",
            "animations/Stand/Question/NAO/Left_Neutral_QUE_03",
            "animations/Stand/Question/NAO/Center_Neutral_QUE_02",
            "animations/Stand/Question/NAO/Center_Strong_QUE_01",
            "animations/Stand/Question/NAO/Center_Neutral_QUE_03",
            "animations/Stand/Question/NAO/Left_Neutral_QUE_01",
            "animations/Stand/Question/NAO/Center_Neutral_QUE_06",
            "animations/Stand/Question/NAO/Right_Neutral_QUE_02",
            "animations/Stand/Question/NAO/Right_Neutral_QUE_01",
        ],
        "space_time": [
            "animations/Stand/Space & time/NAO/Right_Slow_SAT_01",
            "animations/Stand/Space & time/NAO/Center_Slow_SAT_01",
            "animations/Stand/Space & time/NAO/Right_Strong_SAT_06",
            "animations/Stand/Space & time/NAO/Right_Neutral_SAT_10",
            "animations/Stand/Space & time/NAO/Right_Strong_SAT_05",
            "animations/Stand/Space & time/NAO/Right_Neutral_SAT_01",
            "animations/Stand/Space & time/NAO/Center_Neutral_SAT_03",
            "animations/Stand/Space & time/NAO/Left_Neutral_SAT_05",
            "animations/Stand/Space & time/NAO/Right_Neutral_SAT_09",
            "animations/Stand/Space & time/NAO/Left_Neutral_SAT_09",
            "animations/Stand/Space & time/NAO/Right_Neutral_SAT_03",
            "animations/Stand/Space & time/NAO/Right_Neutral_SAT_04",
            "animations/Stand/Space & time/NAO/Left_Neutral_SAT_06",
            "animations/Stand/Space & time/NAO/Center_Strong_SAT_01",
            "animations/Stand/Space & time/NAO/Left_Strong_SAT_05",
            "animations/Stand/Space & time/NAO/Right_Neutral_SAT_05",
            "animations/Stand/Space & time/NAO/Center_Neutral_SAT_01",
            "animations/Stand/Space & time/NAO/Center_Slow_SAT_03",
            "animations/Stand/Space & time/NAO/Right_Neutral_SAT_07",
            "animations/Stand/Space & time/NAO/Left_Strong_SAT_06",
            "animations/Stand/Space & time/NAO/Center_Slow_SAT_02",
            "animations/Stand/Space & time/NAO/Right_Strong_SAT_02",
            "animations/Stand/Space & time/NAO/Right_Neutral_SAT_08",
            "animations/Stand/Space & time/NAO/Left_Strong_SAT_02",
            "animations/Stand/Space & time/NAO/Left_Neutral_SAT_01",
            "animations/Stand/Space & time/NAO/Left_Slow_SAT_01",
            "animations/Stand/Space & time/NAO/Left_Neutral_SAT_03",
            "animations/Stand/Space & time/NAO/Left_Strong_SAT_01",
            "animations/Stand/Space & time/NAO/Left_Neutral_SAT_02",
            "animations/Stand/Space & time/NAO/Right_Neutral_SAT_06",
            "animations/Stand/Space & time/NAO/Left_Neutral_SAT_10",
            "animations/Stand/Space & time/NAO/Left_Neutral_SAT_08",
            "animations/Stand/Space & time/NAO/Left_Strong_SAT_04",
            "animations/Stand/Space & time/NAO/Left_Neutral_SAT_04",
            "animations/Stand/Space & time/NAO/Left_Strong_SAT_03",
            "animations/Stand/Space & time/NAO/Center_Neutral_SAT_02",
            "animations/Stand/Space & time/NAO/Right_Strong_SAT_01",
            "animations/Stand/Space & time/NAO/Center_Strong_SAT_02",
            "animations/Stand/Space & time/NAO/Right_Strong_SAT_03",
            "animations/Stand/Space & time/NAO/Left_Neutral_SAT_07",
            "animations/Stand/Space & time/NAO/Center_Neutral_SAT_04",
            "animations/Stand/Space & time/NAO/Right_Neutral_SAT_02",
            "animations/Stand/Space & time/NAO/Right_Strong_SAT_04",
        ],
    },
    "enjoyment": {
        "default": [
            "animations/Stand/Exclamation/NAO/Center_Strong_EXC_08",
            "animations/Stand/Exclamation/NAO/Center_Slow_EXC_03",
            "animations/Stand/Exclamation/NAO/Center_Strong_EXC_10",
            "animations/Stand/Exclamation/NAO/Left_Neutral_EXC_05",
            "animations/Stand/Exclamation/NAO/Center_Neutral_EXC_05",
            "animations/Stand/Exclamation/NAO/Right_Strong_EXC_01",
            "animations/Stand/Exclamation/NAO/Right_Strong_EXC_04",
            "animations/Stand/Exclamation/NAO/Center_Neutral_EXC_06",
            "animations/Stand/Exclamation/NAO/Left_Strong_EXC_01",
            "animations/Stand/Exclamation/NAO/Center_Neutral_EXC_01",
            "animations/Stand/Exclamation/NAO/Center_Strong_EXC_05",
            "animations/Stand/Exclamation/NAO/Right_Strong_EXC_02",
            "animations/Stand/Exclamation/NAO/Center_Neutral_EXC_07",
            "animations/Stand/Exclamation/NAO/Left_Strong_EXC_04",
            "animations/Stand/Exclamation/NAO/Right_Neutral_EXC_02",
            "animations/Stand/Exclamation/NAO/Left_Strong_EXC_03",
            "animations/Stand/Exclamation/NAO/Center_Strong_EXC_09",
            "animations/Stand/Exclamation/NAO/Center_Strong_EXC_04",
            "animations/Stand/Exclamation/NAO/Center_Neutral_EXC_04",
            "animations/Stand/Exclamation/NAO/Left_Neutral_EXC_02",
            "animations/Stand/Exclamation/NAO/Left_Strong_EXC_02",
            "animations/Stand/Exclamation/NAO/Center_Neutral_EXC_03",
            "animations/Stand/Exclamation/NAO/Center_Neutral_EXC_02",
            "animations/Stand/Exclamation/NAO/Center_Neutral_EXC_08",
            "animations/Stand/Exclamation/NAO/Center_Slow_EXC_02",
            "animations/Stand/Exclamation/NAO/Center_Strong_EXC_06",
            "animations/Stand/Exclamation/NAO/Center_Strong_EXC_03",
            "animations/Stand/Exclamation/NAO/Right_Neutral_EXC_05",
            "animations/Stand/Exclamation/NAO/Right_Strong_EXC_03",
            "animations/Stand/Exclamation/NAO/Center_Slow_EXC_01",
        ]
    },
    "scary": {  # Mapped from 'angry' / 'scary'
        "default": [
            "animations/Stand/Gestures/Reject_1",
            "animations/Stand/Gestures/Reject_2",
            "animations/Stand/Gestures/Reject_3",
            "animations/Stand/Gestures/Reject_4",
            "animations/Stand/Gestures/Reject_5",
            "animations/Stand/Gestures/Reject_6",
            "animations/Stand/Gestures/No_6",
            "animations/Stand/Gestures/No_5",
            "animations/Stand/Gestures/No_8",
            "animations/Stand/Gestures/No_1",
            "animations/Stand/Gestures/No_2",
            "animations/Stand/Gestures/No_9",
            "animations/Stand/Gestures/No_7",
            "animations/Stand/Gestures/No_3",
            "animations/Stand/Gestures/No_4",            
        ]
    },
    "sadness": {
        "default": [
            "animations/Stand/Gestures/Desperate_1",
            "animations/Stand/Gestures/Desperate_2",
            "animations/Stand/Gestures/Desperate_3",
            "animations/Stand/Gestures/Desperate_4",
            "animations/Stand/Gestures/Desperate_5",
            "animations/Stand/Gestures/WhatSThis_13", 
        ]
    },
}

# Flattened list for backward compatibility if needed, or we can just use the helper
ANIMATIONS = {}
for intent, categories in ANIMATIONS_BY_CATEGORY.items():
    ANIMATIONS[intent] = []
    for cat_anims in categories.values():
        ANIMATIONS[intent].extend(cat_anims)

def get_best_animation(intent: str, text: str = "") -> str:
    """
    Selects the best animation based on intent and optional text context.
    """
    if intent not in ANIMATIONS_BY_CATEGORY:
        return None

    categories = ANIMATIONS_BY_CATEGORY[intent]
    
    # If there's only one category (e.g. angry, sadness), just pick from it
    if len(categories) == 1:
        return random.choice(list(categories.values())[0])

    # For neutral (or story telling), we try to match text to categories
    if (intent == "neutral" or intent == "start_story") and text:
        text_lower = text.lower()
        
        # Keywords for categories
        if "?" in text or any(w in text_lower for w in ["what", "where", "who", "why", "how", "when"]):
            return random.choice(categories["question"])
            
        if any(w in text_lower for w in ["no", "not", "never", "don't", "can't", "won't", "nothing"]):
            return random.choice(categories["negation"])
            
        if any(w in text_lower for w in ["i", "me", "my", "mine", "you", "your", "we", "us", "he", "she", "they"]):
            return random.choice(categories["self_others"])
            
        if any(w in text_lower for w in ["one", "two", "three", "first", "second", "third", "next", "then", "finally", "list"]):
            return random.choice(categories["enumeration"])
            
        if any(w in text_lower for w in ["here", "there", "now", "later", "today", "tomorrow", "yesterday", "far", "near"]):
            return random.choice(categories["space_time"])

    # Default fallback: BodyLanguage for neutral/story, or random for others
    if "body_language" in categories or (intent == "start_story" and "body_language" in ANIMATIONS_BY_CATEGORY["neutral"]):
        # If start_story doesn't have its own body_language, use neutral's
        if intent == "start_story":
             return random.choice(ANIMATIONS_BY_CATEGORY["neutral"]["body_language"])
        return random.choice(categories["body_language"])
    
    # Fallback to any random animation in the intent
    all_anims = []
    for cat_anims in categories.values():
        all_anims.extend(cat_anims)
    return random.choice(all_anims)
