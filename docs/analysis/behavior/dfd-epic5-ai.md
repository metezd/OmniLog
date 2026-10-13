# Epic 5 FDD: Recommendation Engine, Spoiler Detection and Embedding Structure

This document explains OmniLog’s AI-focused features within the scope of Epic 5 and their impact on the data model. The key focus areas are as follows:

- recommendation engine
- spoiler detection
- integration of the embedding table into the data model
- the proposed storage approach for the vector space
- review results on the E-R model

## 1. Purpose and scope

Epic 5 comprises the following three core components aimed at enhancing the user experience:

1. Generating personalised recommendations based on the user’s media history and preferences.
2. Detecting spoiler-containing expressions in user reviews.
3. Representing visual, textual and behavioural signals in a common embedding space.

In this context, the data model must encompass not only the relationship between the user and the media, but also the embedding information generated in the background.

## 2. Domain Model and Workflow

### 2.1 Core Entities

- User: a user registered in the system
- MediaItem: a record of a game, TV series or film in the catalogue
- UserLibrary: the user’s personal relationship with media
- Review / Journal Entry: user reviews and ratings
- MediaEmbedding: a table holding content embedding information
- UserPreferenceEmbedding: user profile embedding information

### 2.2 Workflow

1. The user adds, watches, rates or comments on media.
2. The system collects user behaviour data and media metadata.
3. User and media i

Translated with DeepL.com (free version)
