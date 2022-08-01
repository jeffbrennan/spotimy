source("C:/Users/jeffb/Desktop/Life/personal-projects/util.R")
setwd('..')

fantano_vids = fread('reviews/fantano.csv', sep = '\t')

# TODO: fix remaining score parse issues
Extract_Score = function(raw_text){
  raw_score = str_match_all(raw_text, '\\n\\n(.*)\\/10')[[1]][,2]
  # raw_score = str_extract_all(str_squish(raw_text), '\\d{1,2}/\\d{1,2}')[[1]]
  
  output = ifelse(length(raw_score) != 0, raw_score[1], NA)
  return(output)
}

fantano_album_reviews = fantano_vids |> 
  mutate(is_album_review = str_detect(str_to_upper(vid_title), 'REVIEW')
                            & !str_detect(str_to_upper(vid_title), 'YUNOREVIEW')
         ) |> 
  filter(is_album_review) |> 
  mutate(vid_title = ifelse(vid_id == 'VVV0N2Z3QWhYRHkzb05GVEF6RjJvOFB3LmNyWk5ja1Y1UTc0',
                            'Silk Sonic - An Evening With...',
                            vid_title)
         ) |> 
  mutate(artist_album = str_replace_all(vid_title, 'ALBUM REVIEW|MIXTAPE REVIEW|EP REVIEW|NOT GOOD', '')) |>
  mutate(artist_album = str_squish(artist_album)) |> 
  separate(artist_album, into = c('artist', 'album'), sep = '-') |> 
  mutate(across(c(artist, album), str_squish)) |> 
  mutate(is_not_good = str_detect(vid_title, 'NOT GOOD')) |> 
  filter(!is.na(album)) |> 
  filter(!is.na(vid_description)) |> 
  mutate(row_num = row_number()) |> 
  rowwise() |> 
  mutate(score = ifelse(is_not_good,
                        'NOT GOOD',
                        Extract_Score(vid_description)
                        )
         ) |> 
  ungroup()
