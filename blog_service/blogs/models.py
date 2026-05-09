from mongoengine import Document, StringField, ListField, DateTimeField, IntField
import datetime

class Upload(Document):
    user_id = StringField(required=True, max_length=255)
    title = StringField(required=True, max_length=255)
    description = StringField()
    images = ListField(StringField())
    created_at = DateTimeField(default=datetime.datetime.utcnow)
    
    meta = {
        'collection': 'uploads',
        'indexes': [
            'user_id',
            '-created_at'
        ],
        'ordering': ['-created_at']
    }
    
    def __str__(self):
        return self.title