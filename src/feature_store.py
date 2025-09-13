import redis
import json

class RedisFeatureStore:
    # connects to docker container where redis conatiner is running
    def __init__(self, host="localhost", port=6379, db=0):
        self.client = redis.StrictRedis(
            host=host,
            port=port,
            db = db,
            decode_responses=True
        )

###   STORING ROW BY ROW IN JSON FORMAT -- AFTER DATA PROCESSING
    def store_features(self, entity_id, features):
        key =f"entity:{entity_id}:features"
        self.client.set(key, json.dumps(features))

#### GETTING ROWS ONE AT A TIME --REQIURE WHILE MODEL TRAIING 
    def get_features(self, entity_id):
        key =f"entity:{entity_id}:features"
        features = self.client.get(key)

        if features:
            return json.loads(features)
        return None
    
#### STORING IN BATCHES FOR EFFICEINCY
    def store_batch_features(self, batch_data):
        for entity_id, features in batch_data.items():
            self.store_features(entity_id,features)

#### RETRIEVING IN BATCHES
    def get_batch_features(self, entity_ids):
        batch_features = {}
        for entity_id in entity_ids:
            batch_features[entity_id] = self.get_features(entity_id)
        return batch_features
    
    def get_all_entiy_ids(self):  ## ALL ENTITY IDS ARE STORED IN REDIS CLIENT IN THE FORM OF KEYS
        keys = self.client.keys('entity:*:features') # entity: entity_id : feature
        entity_ids = [key.split(':')[1] for key in keys]
        return entity_ids