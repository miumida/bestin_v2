# BESTIN v2

![HAKC)][hakc-shield]
![HACS][hacs-shield]
![Version v1.4][version-shield]

BESTIN v2 월패드 제어를 위한 Custom Integration 입니다.

<br>

## 주의사항
- 장치의 모든 기능을 이용하려면 제조사의 정식 서비스를 이용하시기 바랍니다.
- 본 Component는 제조사의 정식 서비스를 이용하지 못하는 사용자에 한해 개인적인 용도로만 사용하기를 권장합니다.
- 본 Component의 사용책임은 전적으로 사용자에게 있습니다.

<br>

## Change History
| 버전 | 날짜 | 내용 | 
|-----|-----|-----|
| v.1.0.0 | 2021.09 | 개발중 |

<br>

## 지원기능
| 장치 | 지원여부 | 비고 |
|-----|-----|-----|
| 거실조명 | O | |
| 각실조명 | O | |
| 콘센트 | O | 대기전력차단 지원 |
| 가스벨브 | X |  |
| 온도조절기 | O | |
| 환기 | O | 미풍/약풍/강풍 지원 |
| 도어락 | X | |
| 외출설정 | X | |
| 에너지| O | |

<br>



## 테스트
|단지명|진행상태|거실조명|각실조명|콘센트|가스벨브|온도조절기|환기|도어락|외출설정|에너지|비고|
|-------|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|
|강릉회산 한신더휴|테스트중| O | X | △ | X | O | X | X | X | O | - 원가절감형<br>- 조명은 거실조명만 제어<br>- 콘센트는 안방콘센트만 제어|
|목동센트럴아이파크위브 3블럭|테스트중| O | O | O | X | O | O | X | X | O | |


<br>

## 관련사이트
[1] 밍밍1님의 bestin-ha-config github repository(<https://github.com/gaussian8/bestin-ha-config>)<br>



[version-shield]: https://img.shields.io/badge/version-v1.0.0-orange.svg
[hakc-shield]: https://img.shields.io/badge/HAKC-Enjoy-blue.svg
[hacs-shield]: https://img.shields.io/badge/HACS-Custom-red.svg
