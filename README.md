# Development Setup Guide

## Quick Start

1. **Install dependencies** (first time only):
   ```bash
   npm install
   ```

2. **Build CSS** (when you make changes to `src/input.css`):
   ```bash
   npm run build:css
   ```

3. **Watch for CSS changes** (during development):
   ```bash
   npm run watch:css
   ```

4. **Setup Environment**
   ```bash
   npm run setup
   ```

4. **Start the backend** (in a separate terminal):
   ```bash
   npm run start
   ```

## File Structure

- `src/input.css` - Your Tailwind input file with custom styles
- `static/css/output.css` - Generated CSS (don't edit this directly)
- `tailwind.config.js` - Tailwind configuration
- `index.html` - Main HTML file

## Making Changes

1. **Add new styles**: Edit `src/input.css`
2. **Configure Tailwind**: Edit `tailwind.config.js`
3. **Rebuild CSS**: Run `npm run build:css`
4. **Refresh browser**: See your changes

## Common Commands

```bash
# Build CSS once
npm run build:css

# Watch for changes (development)
npm run watch:css

# Start backend
npm run start

# Install new dependencies
npm install package-name

# Update dependencies
npm update
```

## Troubleshooting

- **Styles not working?** Run `npm run build:css`
- **CSS not updating?** Check if `output.css` exists in `static/css/`
- **Build errors?** Check `src/input.css` syntax
- **Performance issues?** Make sure you're not including `node_modules` in content paths
