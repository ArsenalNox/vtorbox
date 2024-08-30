docker-compose down
sudo chown rmt_user:rmt_user postgres-data/
sudo chmod -R 777 postgres-data/
docker-compose build
docker-compose up -d
