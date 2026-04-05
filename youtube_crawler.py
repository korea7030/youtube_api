from apiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import datetime
import pandas as pd
import sys


class FactoryYoutubeApi:
    def __init__(self, query_string, api_key):
        self.developer_key = api_key
        self.youtube_service_name = 'youtube'
        self.youtube_api_version = 'v3'
        self.build_youtube = build(self.youtube_service_name, self.youtube_api_version, developerKey=self.developer_key)
        self.q = query_string
    
    def get_youtube_video_ids(self, max_count):
        # youtube = build(self.youtube_service_name, self.youtube_api_version, developerKey=self.developer_key)
        video_ids = []
        loop_flag = True
        next_page_token = None
        # video_df = pd.DataFrame(columns=['videoId', 'title'])
        while loop_flag:
            remaining_count = max_count - len(video_ids)
            if remaining_count <= 0:
                break

            request = self.build_youtube.search().list(
                q=self.q,
                part='snippet',
                type='video',
                pageToken=next_page_token,
                maxResults=min(50, remaining_count),
            )
            try:
                res = request.execute()
            except HttpError as e:
                print(f'YouTube Search API 요청 실패: {e}')
                print('API 키 제한 설정 또는 YouTube Data API v3 활성화 상태를 확인하세요.')
                return []

            items = res.get('items')

            for item in items:
                print(item['id']['videoId'])
                print(item['snippet']['title'])
                video_ids.append(item['id']['videoId'])
                # tmp = {'videoId': item['id']['videoId'], 'title': item['snippet']['title']}
                # video_df = video_df.append(tmp, ignore_index=True)

                if len(video_ids) >= max_count:
                    loop_flag = False
                    break
            
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
            )

            try:
                response = video_id_list.execute()
            except HttpError as e:
                print(f'Video API 요청 실패(video_id={video_id}): {e}')
                continue

            # 제목
            title_list.append(response['items'][0]['snippet'].get('title'))
            # 영상 링크
            video_link_list.append(f'https://www.youtube.com/watch?v={video_id}')
            # Channel title 입력
            channel_title_list.append(response['items'][0]['snippet'].get('channelTitle'))
            # 영상 업로드 날짜
            publish_at_list.append((datetime.strptime(response['items'][0]['snippet'].get('publishedAt'), '%Y-%m-%dT%H:%M:%SZ')).strftime('%Y-%m-%d'))
            # 조회수 입력
            view_count_list.append(response['items'][0]['statistics'].get('viewCount'))
            # 태그
            tag_list.append(response['items'][0]['snippet'].get('tags'))

        # for title_plus_rating in zip(title_list, channel_title_list, publish_at_list, view_count_list, tag_list):
        #     dicts[title_plus_rating[0]] = int(title_plus_rating[1])
        # sdicts = sorted(dicts.items(), key=operator.itemgetter(1), reverse=True)
        df = pd.DataFrame({'title': title_list, 'video_link': video_link_list, 'channel_title': channel_title_list, 'published_at': publish_at_list, 'view_count': view_count_list, 'tags': tag_list})
        return df
    
    def dataframe_to_dsv(self, data_frame, query_string):
        data_frame.to_csv('./{0}.csv'.format(query_string), sep='|', na_rep='', index=False, encoding='utf-8-sig')


def load_api_key_from_env(env_path='.env'):
    with open(env_path, 'r', encoding='utf-8') as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line or line.startswith('#'):
                continue

            if '=' not in line:
                continue

            key, value = line.split('=', 1)
            if key.strip() == 'api_key':
                return value.strip().strip('"').strip("'")

    return None

if __name__ == '__main__':
    # 검색어
    if len(sys.argv) not in (2, 3):
        print('사용법: python youtube_crawler.py <검색어> [건수]')
        sys.exit()

    max_count = 50
    if len(sys.argv) == 3:
        try:
            max_count = int(sys.argv[2])
            if max_count <= 0:
                raise ValueError
        except ValueError:
            print('건수는 1 이상의 정수여야 합니다.')
            sys.exit(1)

    # api key
    api_key = load_api_key_from_env('.env')
    if not api_key:
        print('.env 파일에서 api_key를 찾지 못했습니다.')
        sys.exit(1)

    query_string = sys.argv[1]
    factory_api = FactoryYoutubeApi(query_string, api_key)
    video_ids = factory_api.get_youtube_video_ids(max_count)
    if not video_ids:
        print('수집할 영상이 없어 종료합니다.')
        sys.exit(1)

    video_dataframe = factory_api.get_video_info_use_video_id(video_ids)

    video_dataframe['published_at'] = pd.to_datetime(video_dataframe['published_at'])
    video_dataframe = video_dataframe.sort_values(by='published_at', ascending=True)

    print("\n=== 검색 결과 ===\n")
    result_df = video_dataframe[['video_link', 'title', 'channel_title', 'view_count']]
    result_df.columns = ['영상URL', '제목', '채널명', '조회수']
    print(result_df.to_string(index=False))
    print(f"\n총 {len(result_df)}건 조회됨\n")
