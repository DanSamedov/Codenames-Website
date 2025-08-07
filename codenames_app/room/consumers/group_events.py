import json

class GroupEventHandlers:
    @staticmethod
    def send_action(consumer, action, **kwargs):
        consumer.send(text_data=json.dumps({
            "action": action,
            **kwargs
        }))

    @staticmethod
    def player_join(consumer, event):
        GroupEventHandlers.send_action(consumer, 'player_join', username=event['username'], role=event['role'], team=event['team'])

    @staticmethod
    def team_choice(consumer, event):
        GroupEventHandlers.send_action(consumer, 'team_choice', username=event['username'], role=event['role'], team=event['team'])

    @staticmethod
    def restrict_choice(consumer, event):
        GroupEventHandlers.send_action(consumer, 'restrict_choice')

    @staticmethod
    def redirect_players(consumer, event):
        GroupEventHandlers.send_action(consumer, 'redirect', room_id=event['room_id'])

    @staticmethod
    def unready_players(consumer, event):
        GroupEventHandlers.send_action(consumer, 'unready', creator=event['creator'])

    @staticmethod
    def player_leave(consumer, event):
        GroupEventHandlers.send_action(consumer, 'player_leave', username=event['username'])
