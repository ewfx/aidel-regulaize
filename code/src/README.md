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