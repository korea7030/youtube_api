from apiclient.discovery import build
from datetime import datetime
import json
import pandas as pd
import sys


class FactoryYoutubeApi:
    def __init__(self, query_string, api_key):
        self.developer_key = api_key
        self.youtube_service_name = 'youtube'
        self.youtube_api_version = 'v3'
        self.build_youtube = build(self.youtube_service_name, self.youtube_api_version, developerKey=self.developer_key)
        self.q = query_string
    
    def get_youtube_video_ids(self):
        # youtube = build(self.youtube_service_name, self.youtube_api_version, developerKey=self.developer_key)
        video_ids = []
        loop_flag = True
        next_page_token = None
        # video_df = pd.DataFrame(columns=['videoId', 'title'])
        while loop_flag:
            request = self.build_youtube.search().list(q=self.q, part='snippet',type='video', pageToken=next_page_token, maxResults=50)
            res = request.execute()

            items = res.get('items')

            for item in items:
                print(item['id']['videoId'])
                print(item['snippet']['title'])
                video_ids.append(item['id']['videoId'])
                # tmp = {'videoId': item['id']['videoId'], 'title': item['snippet']['title']}
                # video_df = video_df.append(tmp, ignore_index=True)
            
            next_page_token = res.get('nextPageToken')
            if not next_page_token:
                loop_flag = False
        
        return video_ids

    def get_video_info_use_video_id(self, video_ids):
        title_list = []
        video_link_list = []
        channel_title_list = []
        view_count_list = []
        publish_at_list = []
        tag_list = []
        dicts = {}

        for video_id in video_ids:
            video_id_list = self.build_youtube.videos().list(
                part='snippet, statistics',
                id=video_id,
            ).execute()

            # 제목
            title_list.append(video_id_list['items'][0]['snippet'].get('title'))
            # 영상 링크
            video_link_list.append(f'https://www.youtube.com/watch?v={video_id}')
            # Channel title 입력
            channel_title_list.append(video_id_list['items'][0]['snippet'].get('channelTitle'))
            # 영상 업로드 날짜
            publish_at_list.append((datetime.strptime(video_id_list['items'][0]['snippet'].get('publishedAt'), '%Y-%m-%dT%H:%M:%SZ')).strftime('%Y-%m-%d'))
            # 조회수 입력
            view_count_list.append(video_id_list['items'][0]['statistics'].get('viewCount'))
            # 태그
            tag_list.append(video_id_list['items'][0]['snippet'].get('tags'))

        # for title_plus_rating in zip(title_list, channel_title_list, publish_at_list, view_count_list, tag_list):
        #     dicts[title_plus_rating[0]] = int(title_plus_rating[1])
        # sdicts = sorted(dicts.items(), key=operator.itemgetter(1), reverse=True)
        df = pd.DataFrame({'title': title_list, 'video_link': video_link_list, 'channel_title': channel_title_list, 'published_at': publish_at_list, 'view_count': view_count_list, 'tags': tag_list})
        return df
    
    def dataframe_to_dsv(self, data_frame, query_string):
        data_frame.to_csv('./{0}.csv'.format(query_string), sep='|', na_rep='', index=False, encoding='utf-8-sig')

if __name__ == '__main__':
    # 검색어
    if len(sys.argv) != 2:
        print('검색어 입력 필요')
        sys.exit()

    # api key
    api_key = None
    with open('.env') as f:
        json_data = json.load(f)
        api_key = json_data.get('api_key')

    query_string = sys.argv[1]
    factory_api = FactoryYoutubeApi(query_string, api_key)
    video_ids = factory_api.get_youtube_video_ids()
    video_dataframe = factory_api.get_video_info_use_video_id(video_ids)

    video_dataframe['published_at'] = pd.to_datetime(video_dataframe['published_at'])
    video_dataframe = video_dataframe.sort_values(by='published_at', ascending=True)
    factory_api.dataframe_to_dsv(video_dataframe, query_string)

    print('Done')
