# Deployment Guide

This guide covers deploying the Gemator application to various cloud platforms.

## Prerequisites

Before deployment:
1. Test the application locally
2. Ensure all dependencies are in `requirements.txt`
3. Have your Gemini API key ready
4. Choose a deployment platform

## Platform Options

### Option 1: Railway

Railway offers simple deployment with PostgreSQL support and automatic HTTPS.

#### Steps:

1. **Install Railway CLI**
```bash
npm i -g @railway/cli
```

2. **Login to Railway**
```bash
railway login
```

3. **Initialize project**
```bash
cd /path/to/gemator
railway init
```

4. **Set environment variables**
```bash
railway variables set GEMINI_API_KEY=your_key_here
railway variables set FLASK_ENV=production
railway variables set MAX_UPLOAD_SIZE=10485760
```

5. **Deploy**
```bash
railway up
```

6. **Get deployment URL**
```bash
railway domain
```

#### Railway Configuration

Create `railway.json`:
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "gunicorn app:app",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

### Option 2: Fly.io

Fly.io provides global deployment with automatic scaling.

#### Steps:

1. **Install Fly CLI**
```bash
curl -L https://fly.io/install.sh | sh
```

2. **Login to Fly**
```bash
flyctl auth login
```

3. **Launch application**
```bash
cd /path/to/gemator
flyctl launch
```

4. **Set secrets**
```bash
flyctl secrets set GEMINI_API_KEY=your_key_here
flyctl secrets set FLASK_ENV=production
```

5. **Deploy**
```bash
flyctl deploy
```

#### Fly.io Configuration

Create `fly.toml`:
```toml
app = "gemator"
primary_region = "sjc"

[build]

[env]
  FLASK_ENV = "production"
  MAX_UPLOAD_SIZE = "10485760"

[http_service]
  internal_port = 5000
  force_https = true
  auto_stop_machines = true
  auto_start_machines = true
  min_machines_running = 0
  processes = ["app"]

[[vm]]
  cpu_kind = "shared"
  cpus = 1
  memory_mb = 256
```

### Option 3: Render

Render provides free tier with automatic builds from Git.

#### Steps:

1. **Push code to GitHub**
```bash
git remote add origin https://github.com/yourusername/gemator.git
git push -u origin main
```

2. **Create Web Service on Render**
   - Go to [render.com](https://render.com)
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Select `gemator` repository

3. **Configure service**
   - Name: `gemator`
   - Environment: `Python 3`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`

4. **Set environment variables**
   - `GEMINI_API_KEY`: your_key_here
   - `FLASK_ENV`: production
   - `MAX_UPLOAD_SIZE`: 10485760

5. **Deploy**
   - Click "Create Web Service"
   - Render will auto-deploy on every push to main

### Option 4: Heroku

Heroku offers easy deployment with extensive add-ons.

#### Steps:

1. **Install Heroku CLI**
```bash
curl https://cli-assets.heroku.com/install.sh | sh
```

2. **Login**
```bash
heroku login
```

3. **Create app**
```bash
cd /path/to/gemator
heroku create gemator-app
```

4. **Set environment variables**
```bash
heroku config:set GEMINI_API_KEY=your_key_here
heroku config:set FLASK_ENV=production
heroku config:set MAX_UPLOAD_SIZE=10485760
```

5. **Deploy**
```bash
git push heroku main
```

6. **Open app**
```bash
heroku open
```

#### Heroku Configuration

Create `Procfile`:
```
web: gunicorn app:app
```

Create `runtime.txt`:
```
python-3.11.0
```

## Production Considerations

### 1. Add Gunicorn

Update `requirements.txt`:
```
Flask==3.0.0
google-generativeai==0.3.0
Pillow>=10.0.0
opencv-python>=4.8.0
python-dotenv==1.0.0
gunicorn==21.2.0
```

### 2. Configure Production Settings

Update `app.py` for production:
```python
if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)
```

### 3. Security Enhancements

- Enable HTTPS (automatic on most platforms)
- Set up CORS if needed
- Add rate limiting
- Implement request size validation
- Use environment-specific configs

### 4. File Storage

For production, consider:
- AWS S3 for image storage
- Cloudinary for image processing
- Local storage with cleanup cron jobs

### 5. Monitoring

Set up monitoring for:
- API request counts
- Translation success/failure rates
- Response times
- Error logs

## Environment Variables

All platforms need these environment variables:

| Variable | Description | Example |
|----------|-------------|---------|
| `GEMINI_API_KEY` | Google Gemini API key | `AIzaSy...` |
| `FLASK_ENV` | Environment mode | `production` |
| `MAX_UPLOAD_SIZE` | Max upload bytes | `10485760` |
| `PORT` | Server port (auto-set) | `5000` |

## Post-Deployment

After deployment:

1. **Test the application**
   - Upload test images
   - Verify translations work
   - Check error handling

2. **Set up monitoring**
   - Platform-specific dashboards
   - Error tracking (Sentry)
   - Analytics

3. **Configure custom domain** (optional)
   - Add DNS records
   - Configure SSL
   - Update CORS settings

## Scaling Considerations

As usage grows:

1. **Increase resources**
   - More memory for image processing
   - Additional CPU for concurrent requests

2. **Add caching**
   - Redis for translation cache
   - CDN for static assets

3. **Queue system**
   - Celery for background tasks
   - Redis/RabbitMQ as broker

4. **Database**
   - PostgreSQL for user data
   - Store translation history

## Troubleshooting Deployment

### Build fails
- Check Python version compatibility
- Verify all dependencies in requirements.txt
- Review build logs for missing packages

### App crashes on start
- Check environment variables are set
- Verify Gemini API key is valid
- Review application logs

### Slow performance
- Increase dyno/instance size
- Add caching layer
- Optimize image processing

### File upload issues
- Configure upload size limits
- Check filesystem permissions
- Verify storage availability

## Cost Estimates

### Free Tiers (Starting Point)

- **Railway**: 500 hours/month free
- **Fly.io**: 3 shared-cpu-1x VMs free
- **Render**: 750 hours/month free
- **Heroku**: 1000 dyno hours/month free

### Gemini API Costs

- Free tier: 15 requests/minute
- Paid tier: Higher rate limits
- Monitor usage in Google Cloud Console

## Rollback Procedure

If deployment has issues:

### Railway
```bash
railway rollback
```

### Fly.io
```bash
flyctl releases list
flyctl releases rollback <version>
```

### Render
- Go to dashboard → Deploys
- Click "Rollback" on previous version

### Heroku
```bash
heroku releases
heroku rollback v<number>
```

## Next Steps

1. Set up CI/CD pipeline
2. Add automated testing
3. Configure staging environment
4. Implement logging and monitoring
5. Set up backup strategy

## Support

For platform-specific issues:
- Railway: [docs.railway.app](https://docs.railway.app)
- Fly.io: [fly.io/docs](https://fly.io/docs)
- Render: [render.com/docs](https://render.com/docs)
- Heroku: [devcenter.heroku.com](https://devcenter.heroku.com)
