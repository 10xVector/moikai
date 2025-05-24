from app import app, db
from models import Card, UserExercise
from datetime import datetime

def reset_database():
    with app.app_context():
        # Clear all user attempts and cards
        UserExercise.query.delete()
        Card.query.delete()
        db.session.commit()
        
        # 5 high-quality Japanese paragraph cards
        cards = [
            Card(
                front="私は毎朝コーヒーを飲みます。駅まで歩きます。電車で会社に行きます。\nWatashi wa mai asa koohii o nomimasu. Eki made arukimasu. Densha de kaisha ni ikimasu.",
                back="I drink coffee every morning. I walk to the station. I go to work by train.",
                option_1="A typical morning routine",
                option_2="A family dinner",
                option_3="A school festival",
                option_4="A shopping trip",
                audio_url=None,
                category="Daily Life",
                difficulty="beginner"
            ),
            Card(
                front="今日は雨です。かさを持って出かけます。バスで学校に行きます。\nKyou wa ame desu. Kasa o motte dekakemasu. Basu de gakkou ni ikimasu.",
                back="It is raining today. I go out with an umbrella. I go to school by bus.",
                option_1="Going to school on a rainy day",
                option_2="Playing sports outside",
                option_3="Visiting a museum",
                option_4="Going to the beach",
                audio_url=None,
                category="Weather",
                difficulty="beginner"
            ),
            Card(
                front="母は料理が上手です。毎晩おいしいご飯を作ってくれます。家族みんなで食べます。\nHaha wa ryouri ga jouzu desu. Maiban oishii gohan o tsukutte kuremasu. Kazoku minna de tabemasu.",
                back="My mother is good at cooking. She makes delicious meals every night. The whole family eats together.",
                option_1="Family dinner at home",
                option_2="Eating at a restaurant",
                option_3="Cooking class",
                option_4="Picnic in the park",
                audio_url=None,
                category="Family",
                difficulty="beginner"
            ),
            Card(
                front="週末はよく本を読みます。時々映画も見ます。友達とカフェに行くことも好きです。\nShuumatsu wa yoku hon o yomimasu. Tokidoki eiga mo mimasu. Tomodachi to kafe ni iku koto mo suki desu.",
                back="I often read books on weekends. Sometimes I watch movies. I also like going to cafes with friends.",
                option_1="Weekend leisure activities",
                option_2="Studying for exams",
                option_3="Working overtime",
                option_4="Traveling abroad",
                audio_url=None,
                category="Hobbies",
                difficulty="beginner"
            ),
            Card(
                front="新しいくつがほしいです。デパートで色々見ました。最後に白いくつを買いました。\nAtarashii kutsu ga hoshii desu. Depaato de iroiro mimashita. Saigo ni shiroi kutsu o kaimashita.",
                back="I want new shoes. I looked at various ones in the department store. In the end, I bought white shoes.",
                option_1="Buying new shoes",
                option_2="Returning old shoes",
                option_3="Shopping for groceries",
                option_4="Buying a new phone",
                audio_url=None,
                category="Shopping",
                difficulty="beginner"
            )
        ]
        
        for card in cards:
            db.session.add(card)
        db.session.commit()
        print("Database reset and 5 high-quality paragraph cards added successfully!")

if __name__ == '__main__':
    reset_database() 