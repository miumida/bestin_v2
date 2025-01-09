# BESTIN v2

![HAKC)][hakc-shield]
![HACS][hacs-shield]
![Version v1.0.0][version-shield]

BESTIN v2 월패드 제어를 위한 Custom Integration 입니다.<br>
RS485통신이 가능하다면, 네이버 HA카페의 halwin님의 Component를 사용하시기를 추천합니다.<br>
사용법에 대한 가이드도 제공되지 않으며, 네이버 관련 카페 등에 게시되어 있는 내용을 참고하시기 바랍니다.<br>
공식적인 업데이트나 기능 추가에 대한 요청은 받지 않습니다.<br>

<br>

## 주의사항
- 장치의 모든 기능을 이용하려면 제조사의 정식 서비스를 이용하시기 바랍니다.
- 본 Component는 제조사의 정식 서비스를 이용하지 못하는 사용자에 한해 개인적인 용도로만 사용하기를 권장합니다.
- 본 Component가 단지 서버에 영향을 줄 수 있음을 충분히 인지하고 사용하기를 권장합니다.
- 본 Component의 사용책임은 전적으로 사용자에게 있습니다.

<br>

## Change History
| 버전 | 날짜 | 내용 | 
|-----|-----|-----|
| v.1.0.0 | 2025.01 | END  |

<br>


## now...
- Not optimization now.

<br>

## Installation
### Manual
- HA 설치 경로 아래 custom_components에 bestin_v2폴더 안의 전체 파일을 복사해줍니다.<br>
  `<config directory>/custom_components/bestin_v2/`<br>
- Home-Assistant 를 재시작합니다<br>
### HACS
- HACS > Integretions > 우측상단 메뉴 > Custom repositories 선택
- 'https://github.com/miumida/bestin_v2' 주소 입력, Category에 'integration' 선택 후, 저장
- HACS > Integretions 메뉴 선택 후, BESTIN v2 검색하여 설치

<br>

## 지원기능
| 장치 | 지원여부 | 비고 |
|-----|-----|-----|
| 거실조명 | O | |
| 각실조명 | O | 방 조명 일괄 끄기 지원|
| 콘센트 | O | 대기전력차단 지원 |
| 가스벨브 | O | 닫기만 지원 |
| 온도조절기 | O | |
| 환기 | O | 미풍/약풍/강풍 지원 |
| 도어락 | X | |
| 외출설정 | X | |
| 에너지| O | |

<br>

### 에너지
|구분|지원여부|비고|
|--|--|--|
| 가스 | O | |
| 난방 | O | |
| 수도 | O | |
| 온수 | O | |
| 전기 | O | |


<br>


## 테스트
|단지명|진행상태|거실조명|각실조명|콘센트|가스벨브|온도조절기|환기|도어락|외출설정|에너지|비고|
|-------|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|
|강릉회산 한신더휴| 사용자 테스트중| O | X | △ | O | O | X | X | X | O | - 원가절감형<br>- 조명은 거실조명만 제어<br>- 콘센트는 안방콘센트만 제어|
|목동센트럴아이파크위브 3블럭| 사용자 테스트중| O | O | O | O | O | O | X | X | O | |
|김포사우| 사용자 테스트중| O | O | O | O | O | O | X | X | O | - ROOM1이 거실, ROOM2가 방1 |
|파주운정아이파크| 사용자 테스트중| O | O | O | O | O | O | X | X | O | 스마트 조명 |
|시흥배곧C1호반써밋플레이스| 사용자 테스트중 | O | X | X | O | O | O | X | X | O |  |
|병점역아이파크캐슬 | 사용자 테스트중 | O | O | O | O | O | O | X | X | O |  |
|구리갈매역 | 사용자 테스트중 | O | O | O | O | O | O | X | X | O |  |
|당진수청한라비발디 | 사용자 테스트중 | O | X | X | O | O | O | X | X | O |  |
|꿈의숲아이파크 | 사용자 테스트중 | O | O | O | O | O | O | X | X | O |  |
|대전아이파크시티1단지 | 사용자 테스트중 | O | O | O | X | O | O | X | X | O |  |
|백련산SK뷰 | 사용자 테스트중 | O | O | O | O | O | O | X | X | O |  |
|양산물금브라운스톤 |사용자 테스트중 | O | O | O | O | O | O | X | X | O |  |
<br>

## 관련사이트
[1] 네이버 SmartThings & IoT Community카페 | 개발자88님의 "[설정팁]BESTIN 2.0 전등/콘센트/환기/난방 제어 성공하였습니다." 게시글(<https://cafe.naver.com/stsmarthome/38266>)<br>
[2] 밍밍1님의 bestin-ha-config github repository(<https://github.com/gaussian8/bestin-ha-config>)<br>



[version-shield]: https://img.shields.io/badge/version-v1.0.0-orange.svg
[hakc-shield]: https://img.shields.io/badge/HAKC-Enjoy-blue.svg
[hacs-shield]: https://img.shields.io/badge/HACS-Custom-red.svg
