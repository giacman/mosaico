# Cloud Storage Setup for Few-Shot Examples

This guide explains how to set up Cloud Storage for production-ready few-shot learning examples.

## 🎯 Why Cloud Storage?

Currently, few-shot examples are hardcoded in `backend/app/api/generate.py`. 

Moving to Cloud Storage allows:
- ✅ Update examples without redeploying backend
- ✅ Version control for prompts
- ✅ A/B testing different examples
- ✅ Easy management via UI (future Phase 2)

## 📁 Recommended Structure

```
gs://mosaico-examples/
├── newsletter/
│   ├── professional/
│   │   ├── example_1.json
│   │   ├── example_2.json
│   │   └── example_3.json
│   ├── enthusiastic/
│   │   ├── example_1.json
│   │   └── example_2.json
│   └── casual/
│       └── example_1.json
├── social_post/
│   └── professional/
│       └── example_1.json
└── product_description/
    └── professional/
        └── example_1.json
```

## 🚀 Setup Instructions

### 1. Create GCS Bucket

```bash
# Create bucket (EU region)
gsutil mb -l europe-west1 gs://mosaico-examples

# Make it private (default)
gsutil iam ch allUsers:objectViewer gs://mosaico-examples  # DON'T DO THIS
# Keep it private, only service account access
```

### 2. Create Example Files

Create `example_1.json`:
```json
{
  "input": "Nuova collezione primavera",
  "output": [
    "Scopri la nuova collezione primavera/estate",
    "La collezione PE2025 ti aspetta",
    "Novità stagionali: esplora la gamma"
  ],
  "metadata": {
    "tone": "professional",
    "content_type": "newsletter",
    "language": "it",
    "quality_score": 5
  }
}
```

### 3. Upload Examples

```bash
# Upload single file
gsutil cp example_1.json gs://mosaico-examples/newsletter/professional/

# Upload directory
gsutil -m cp -r examples/* gs://mosaico-examples/
```

### 4. Grant Backend Access

```bash
# Get Cloud Run service account
gcloud run services describe mosaico-backend \
  --region europe-west1 \
  --format='value(spec.template.spec.serviceAccountName)'

# Grant Storage Object Viewer role
gsutil iam ch serviceAccount:YOUR_SERVICE_ACCOUNT:objectViewer gs://mosaico-examples
```

### 5. Update Backend Code

Replace `load_few_shot_examples()` in `backend/app/api/generate.py`:

```python
from google.cloud import storage
import json

def load_few_shot_examples(content_type: str, tone: str) -> str:
    """Load few-shot examples from Cloud Storage"""
    
    client = storage.Client()
    bucket = client.bucket(settings.gcs_bucket_examples)
    
    # List all examples for this content_type and tone
    prefix = f"{content_type}/{tone}/"
    blobs = bucket.list_blobs(prefix=prefix)
    
    examples = []
    for blob in blobs:
        if blob.name.endswith('.json'):
            content = blob.download_as_text()
            example = json.loads(content)
            examples.append(example)
    
    # Sort by quality_score if available
    examples.sort(
        key=lambda x: x.get('metadata', {}).get('quality_score', 0),
        reverse=True
    )
    
    # Take top 3 examples
    examples = examples[:3]
    
    # Format for prompt
    formatted_examples = []
    for i, ex in enumerate(examples, 1):
        formatted_examples.append(
            f"Example {i}:\\n"
            f"Input: \\"{ex['input']}\\"\\n"
            f"Output: {json.dumps(ex['output'], ensure_ascii=False)}"
        )
    
    return "\\n\\n".join(formatted_examples)
```

## 📊 Example Quality Management

Add `quality_score` to examples based on user feedback:

```json
{
  "input": "...",
  "output": [...],
  "metadata": {
    "quality_score": 5,  // 1-5 based on user ratings
    "created_at": "2025-01-15",
    "updated_at": "2025-01-20",
    "usage_count": 145,  // How many times used
    "success_rate": 0.92  // % of thumbs up
  }
}
```

## 🧪 A/B Testing (Phase 2)

Structure for A/B testing:

```
gs://mosaico-examples/
├── newsletter/
│   ├── professional/
│   │   ├── variant_a/
│   │   │   ├── example_1.json
│   │   │   └── example_2.json
│   │   └── variant_b/
│   │       ├── example_1.json
│   │       └── example_2.json
```

Load based on user segment or random assignment.

## 🔄 Versioning

Use object versioning in GCS:

```bash
# Enable versioning
gsutil versioning set on gs://mosaico-examples

# List versions
gsutil ls -a gs://mosaico-examples/newsletter/professional/example_1.json

# Restore old version
gsutil cp gs://mosaico-examples/newsletter/professional/example_1.json#123456 \
  gs://mosaico-examples/newsletter/professional/example_1.json
```

## 💰 Cost Estimate

- Storage: ~$0.02/GB/month (negligible for examples)
- Retrieval: ~$0.004 per 10,000 operations
- **Total**: <$1/month for typical usage

## 🎯 Best Practices

1. **Keep Examples Small**: <500 chars per example
2. **Quality Over Quantity**: 3-5 great examples > 20 mediocre
3. **Language Separation**: Different examples per language
4. **Version Control**: Use git for example JSONs too
5. **Backup**: `gsutil -m cp -r gs://mosaico-examples backup/`

## 📝 Management Script (Future)

Create `manage_examples.py`:

```python
#!/usr/bin/env python3
"""Manage few-shot examples in Cloud Storage"""

from google.cloud import storage
import json
import sys

def add_example(content_type, tone, example_data):
    """Add new example to GCS"""
    client = storage.Client()
    bucket = client.bucket('mosaico-examples')
    
    # Generate filename
    existing = list(bucket.list_blobs(prefix=f"{content_type}/{tone}/"))
    next_num = len(existing) + 1
    
    blob_name = f"{content_type}/{tone}/example_{next_num}.json"
    blob = bucket.blob(blob_name)
    
    blob.upload_from_string(
        json.dumps(example_data, ensure_ascii=False, indent=2),
        content_type='application/json'
    )
    
    print(f"✓ Added: {blob_name}")

if __name__ == "__main__":
    # Usage: python manage_examples.py add newsletter professional "input" '["out1", "out2"]'
    pass
```

## 🚀 Next Steps

For Phase 2, build a web UI to:
- Upload new examples
- Edit existing examples
- View analytics (which examples perform best)
- A/B test different example sets

