gcloud functions deploy MorphologyFunction `
    --gen2 `
    --trigger-http `
    --allow-unauthenticated `
    --runtime python310 `
    --region europe-central2 `
    --memory 512MB
