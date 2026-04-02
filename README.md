# Student Support Chatbot - Training Data

This repository contains the training data for a Rasa-based student support chatbot designed to handle university student inquiries.

## Data Overview

The chatbot is trained on domain-specific NLU (Natural Language Understanding) data covering the following topics:

### Training Data Structure (`data/` folder):

- `nlu.yml` - Complete NLU training data with user query examples and their intent labels
- `stories.yml` - Dialogue flow training data showing conversation patterns and responses
- `rules.yml` - Rule-based response patterns for specific scenarios
- `nlu/` - Domain-specific training files:
  - `academics.yml` - Academic-related queries
  - `admissions.yml` - Admissions process inquiries
  - `contact.yml` - Contact information requests
  - `documents.yml` - Student document-related queries
  - `examinations.yml` - Exam-related questions
  - `fees.yml` - Fees and payments inquiries
  - `general.yml` - General college information
  - `grievances.yml` - Complaint and grievance procedures
  - `hostel.yml` - Hostel and accommodation details
  - (and other domain files)

### Configuration Files:

- `domain.yml` - Defines intents, entities, and response templates
- `config.yml` - NLU pipeline and model configuration
- `endpoints.yml` - Action server configuration

## Data Description

### NLU Training Data (`data/nlu/`)

Domain-specific training files containing user query examples and their corresponding intents:

- `general.yml` - Greetings and general queries
- `admissions.yml` - Admissions process questions
- `fees.yml` - Fee structure and payment inquiries  
- `documents.yml` - Certificate and document requests
- `examinations.yml` - Exam schedule and results
- `academics.yml` - Academic programs and courses
- `hostel.yml` - Hostel facilities information
- `contact.yml` - Contact information requests
- `grievances.yml` - Complaint and grievance procedures
- (and other domain files)

### Dialogue Training Data

- `data/nlu.yml` - Combined NLU training data
- `data/stories.yml` - Multi-turn conversation flows
- `data/rules.yml` - Rule-based response patterns

## Configuration Files

- `domain.yml` - Defines intents, entities, and response templates for the chatbot
- `config.yml` - NLU pipeline and model configuration
- `endpoints.yml` - Action server configuration

## Notes

All files are in YAML format compatible with Rasa 3.x framework. The data includes over 1000+ training examples across multiple student support domains.

### FAQ Data Schema (MongoDB Backend)

FAQs are stored in MongoDB with the following structure:

```json
{
  "_id": "ObjectId",
  "question": "User query string",
  "answer": "Response/answer text",
  "category": "Domain category (e.g., General, Admissions, Fees)"
}
```

Field Descriptions:
- `question` - The user's frequently asked question
- `answer` - The corresponding answer/response
- `category` - Classification of the FAQ (aligns with training data domains)


