gcloud functions deploy DictionariesTableFunction `
    --gen2 --trigger-http `
    --allow-unauthenticated `
    --runtime python310 `
    --region europe-central2 `
    --memory 128Mi
