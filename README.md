# 🚀 Project Name

## 📌 Table of Contents
- [Introduction](#introduction)
- [Demo](#demo)
- [Inspiration](#inspiration)
- [What It Does](#what-it-does)
- [How We Built It](#how-we-built-it)
- [Challenges We Faced](#challenges-we-faced)
- [How to Run](#how-to-run)
- [Tech Stack](#tech-stack)
- [Team](#team)

---

## 🎯 Introduction
A brief overview of your project and its purpose. Mention which problem statement are your attempting to solve. Keep it concise and engaging.

## 🎥 Demo
🔗 [Live Demo](#) (if applicable)  
📹 [Video Demo](#) (if applicable)  
🖼️ Screenshots:

![Screenshot 1](link-to-image)

## 💡 Inspiration
What inspired you to create this project? Describe the problem you're solving.

## ⚙️ What It Does
Explain the key features and functionalities of your project.

## 🛠️ How We Built It
Briefly outline the technologies, frameworks, and tools used in development.

## 🚧 Pre-Load OFAC Sanctions List into MongoDB instance
The latest sanction list (published on 21st March 2025) has been downloaded and saved in "static_data/sdn.xml".
To load this data into the mongoDB instance, follow these steps:
1. Provide the MongoDB Sanctions DB and collection name in the .env file:
   ```sh
   MONGO_SANCTIONS_DB=sanctions_db
   MONGO_SANCTIONS_COLLECTION=sdn_list
   ```
2. From the terminal run the following command:
   ```sh
   python3 load_sdn_list.py
   ```

3. If you need to wipe existing data from the mongoDB sanctions database before inserting fresh data, run the script with the --wipe flag (it will ask for confirmation before deleting data from the DB).
   ```sh
   python3 load_sdn_list.py --wipe
   ```

## 🏃 How to Run
1. If you already have an existing Redis and MongoDB instance, provide the config (hostname, port) in ".env" fie situated under code/src

2. If however you do not have existing instances of Redis and/mongodDB you can start your own locally using DOCKER containers. 

3. Ensure you have the DOCKER applicaition installed and running

4. Navigate to code/src and execute this command in the terminal:
   ```sh
   docker-compose up -d
   ```

5. This will startup instances of Redis and MongoDB locally, in the predefined ports provided in .env file

6. To kill the docker instances you can run the below command in terminal:
   ```sh
   docker-compose down
   ```

7. Clone the repository  
   ```sh
   git clone https://github.com/your-repo.git
   ```
8. Install dependencies  
   ```sh
   pip install -r requirements.txt (for Python)
   ```
9. Run the project  
   ```sh
   python main.py

10. To test whether the app has started successfuly you can access the below endpoints:
http://127.0.0.1:8000/
http://127.0.0.1:8000/mongo-test
http://127.0.0.1:8000/redis-test
http://127.0.0.1:8000/docs
   ```

## 🏗️ Tech Stack
- 🔹 Frontend: React / Vue / Angular
- 🔹 Backend: Node.js / FastAPI / Django
- 🔹 Database: PostgreSQL / Firebase
- 🔹 Other: OpenAI API / Twilio / Stripe

## 👥 Team
- **Your Name** - [GitHub](#) | [LinkedIn](#)
- **Teammate 2** - [GitHub](#) | [LinkedIn](#)