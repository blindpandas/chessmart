LICHESS_URL = "https://lichess.org/"

###########
# ACCOUNT #
###########
ACCOUNT_URL = "api/account"
ACCOUNT_EMAIL_URL = "api/account/email"
ACCOUNT_PREFERENCES_URL = "api/account/preferences"
ACCOUNT_KID_URL = "api/account/kid"

#########
# USERS #
#########
USERS_STATUS_URL = "api/users/status"
USERS_PLAYER_URL = "player"
USERS_PLAYER_TOP_URL = "player/top/{nb}/{perfType}"
USERS_USER_PUBLIC_DATA_URL = "api/user/{username}"
USERS_RATING_HISTORY_URL = "api/user/{username}/rating-history"
USERS_ACTIVITY_URL = "api/user/{username}/activity"
USERS_MY_PUZZLE_ACTIVITY_URL = "api/user/puzzle-activity"
USERS_GET_BY_IDS_URL = "api/users"
USERS_TEAM_MEMBERS_URL = "team/{teamId}/users"
USERS_LIVE_STREAMERS_URL = "streamer/live"

#############
# RELATIONS #
#############
RELATIONS_FOLLOWING_URL = "api/user/{username}/following"
RELATIONS_FOLLOWERS_URL = "api/user/{username}/followers"

#########
# GAMES #
#########
GAMES_EXPORT_ONE_URL = "game/export/{gameId}"
GAMES_EXPORT_USER_URL = "api/games/user/{username}"
GAMES_EXPORT_IDS_URL = "games/export/_ids"
GAMES_STREAM_CURRENT_URL = "api/stream/games-by-users"
GAMES_ONGOING_URL = "api/account/playing"
GAMES_CURRENT_TV_URL = "tv/channels"

#########
# TEAMS #
#########
TEAMS_JOIN_URL = "team/{teamId}/join"
TEAMS_LEAVE_URL = "team/{teamId}/quit"
TEAMS_KICK_USER_URL = "/team/{teamId}/kick/{userId}"

########
# BOTS #
########
BOTS_STREAM_INCOMING_EVENTS = "api/stream/event"

##########
# BOARDS #
##########
BOARDS_STREAM_INCOMING_EVENTS = "api/stream/event"
BOARDS_CREATE_A_SEEK = "api/board/seek"
BOARDS_STREAM_GAME_STATE = "api/board/game/stream/{gameId}"
BOARDS_MAKE_MOVE = "api/board/game/{gameId}/move/{move}"
BOARDS_ABORT_GAME = "api/board/game/{gameId}/abort"
BOARDS_RESIGN_GAME = "api/board/game/{gameId}/resign"
BOARDS_WRITE_IN_CHAT = "api/board/game/{gameId}/chat"
BOARDS_HANDLE_DRAW = "api/board/game/{gameId}/draw/{accept}"

##############
# CHALLENGES #
##############
CHALLENGES_CREATE = "api/challenge/{username}"
CHALLENGES_ACCEPT = "api/challenge/{challengeId}/accept"
CHALLENGES_DECLINE = "api/challenge/{challengeId}/decline"

###############
# TOURNAMENTS #
###############
TOURNAMENTS_CURRENT = "api/tournament"
TOURNAMENTS_CREATE = "api/tournament"
TOURNAMENTS_EXPORT_GAMES = "api/tournament/{id}/games"
TOURNAMENTS_EXPORT_RESULTS = "api/tournament/{id}/results"
TOURNAMENTS_GET_CREATED_BY_USER = "api/user/{username}/tournament/created"

###############
# BROADCASTS  #
###############
BROADCASTS_CREATE = "broadcast/new"
BROADCASTS_GET = "broadcast/-/{broadcastId}"
BROADCASTS_PUSH_PGN = "broadcast/-/{broadcastId}/push"

###############
# SIMULATIONS #
###############
SIMULATIONS_GET = "api/simul"

############
# MESSAGES #
############
MESSAGES_SEND = "inbox/{username}"

###########
# STUDIES #
###########
STUDIES_EXPORT_CHAPTER = "study/{studyId}/{chapterId}.pgn"
STUDIES_EXPORT_ALL_CHAPTERS = "study/{studyId}.pgn"
