# Data Dictionary + Feature Feasibility v1.0

| Variable | Nguồn | Direct/Derived | Type | Missing risk | Model v1 | Leakage/Risk |
|---|---|---|---|---|---|---|
| source | crawler | derived | category | Low | No | metadata |
| url | search | direct | string | Low | No | identifier |
| listing_id | detail/URL | direct/derived | string | Low | No | identifier |
| listing_date | detail | direct | date | Medium | Maybe | temporal bias |
| title | search/detail | direct | text | Low | No | có thể chứa giá |
| description | search/detail | direct | text | Low | No | có thể chứa giá |
| transaction_type | scope | derived | category | Low | No | fixed SALE |
| property_type | URL/title/detail | direct/derived | category | Low-Med | Yes | normalization |
| current_ward | location | direct | category | Low | Maybe | admin changes |
| legacy_area | scope map/text | derived | category | Medium | Yes | scope inference |
| city | scope | direct | category | Low | No | constant |
| price_text | page | direct | string | Low | No | raw target |
| price_vnd | parse | derived | float | Critical | **Target** | — |
| displayed_price_per_m2 | page | direct | float/text | Medium | **No** | target leakage |
| area_text | page | direct | string | Low | No | raw |
| area_m2 | parse | derived | float | Critical | Yes | definition risk |
| land_area_m2 | description | derived | float | High | Maybe | parse uncertainty |
| floor_area_m2 | description | derived | float | High | Maybe | parse uncertainty |
| bedrooms | detail/text | direct/parse | float | High | Maybe | missing |
| bathrooms | detail/text | direct/parse | float | High | Maybe | missing |
| floors | detail/text | direct/parse | float | High | Maybe | missing |
| legal_status | detail/text | direct/parse | category | High | Maybe | missing |
| direction | detail | direct | category | High | Maybe | missing |
| road_width_m | detail/text | direct/parse | float | High | Maybe | missing |
| project_name | text/detail | parse | category | High | Maybe | sparse |
| crawl_page | crawler | derived | int | Low | No | metadata |
| crawled_at | crawler | derived | datetime | Low | No | metadata |
| scope_status | scope | derived | category | Low | No | QA |
| area_definition_risk | QA | derived | bool | Low | No | QA flag |

## Bộ feature tối thiểu cần chứng minh ở production

Để BQ01 vẫn khả thi sau crawl, cần tối thiểu:

1. `price_vnd`
2. `area_m2`
3. `property_type`
4. `legacy_area`
5. `listing_date` hoặc update time
6. một/ vài đặc điểm như bedrooms/floors/legal status nếu availability đủ

Nếu nhóm 5–6 không đủ availability, model v1 vẫn có thể bắt đầu bằng:
`area_m2 + property_type + legacy_area`, sau đó mở rộng có điều kiện.
