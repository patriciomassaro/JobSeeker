# Jobseeker Helper

## Description

This project leverages LLMs and linkedin job search to help you with your job search.

It is based on a "human-in-the-loop" workflow that uses the corrections you make to the LLM as feedback.

- You upload your resume and use LLMs to parse it.
- You fill additional info like your hobbies, products you use, etc.
- You search for jobs that fit your criteria
- LLMs will use your info and the job posting to create a tailored resume and cover letter.
- You have an interface to make corrections to the output of the model
    - For example, you can eliminate adverbs, try to make the model to be more specific, change the way it construct the sentences, etc.
-  Your corrections will be used for future calls, and the level of the outputs will improve! 

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
- [Roadmap](#roadmap)

## Installation

> **Note:** Make sure you have docker installed

Add the following env variables:

- GROQ_API_KEY : your key in case you want to use LLama3
- OPENAI_API_KEY: Your key in case you want to use OPEN AI models
- JOBSEEKER_DB_USERNAME: the username of the database
- JOBSEEKER_DB_PASSWORD: the password of the database
- JOBSEEKER_DB_NAME: the name of the POSTGRE database that will be created


Install the project dependencies, run the following command:

```sh
pip install requirements.txt
```

Run this command to spin up the database

```sh
docker-compose -f jobseeker/database/docker-compose.yml up
```

Run the python script that generates all the database tables.

```sh
python3 jobseeker/database/routines/recreate_tables.py
```

Start the flask app:

```sh
cd jobseeker/frontend
flask --app app run
```

## Usage

- Create a user and password
- Upload your CV
- Add all the comments you want to your profile
- Parse your CV with LLMs
- Look for jobs using the job scraping section
- Parse the job descriptions using LLMs
- Build customized CVs and Cover Letters
- Give feedback! This is **crucial**.
- Repeat


## Roadmap

- Use feedback to fine-tune smaller models.
- Use embeddings for semantic job search.

