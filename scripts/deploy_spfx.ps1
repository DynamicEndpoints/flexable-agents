# SharePoint Framework Deployment Script
param(
    [Parameter(Mandatory=$true)]
    [string]$SolutionPath,
    
    [Parameter(Mandatory=$true)]
    [string]$Environment,
    
    [Parameter(Mandatory=$false)]
    [switch]$SkipBuild,
    
    [Parameter(Mandatory=$false)]
    [switch]$SkipTest,
    
    [Parameter(Mandatory=$false)]
    [switch]$Force
)

# Import configuration
$configPath = Join-Path $PSScriptRoot "..\config\templates\sharepoint_dev_config_template.json"
$config = Get-Content $configPath | ConvertFrom-Json

# Validate environment
$validEnvironments = @("dev", "qa", "prod")
if ($validEnvironments -notcontains $Environment) {
    throw "Invalid environment. Must be one of: $($validEnvironments -join ', ')"
}

# Set up environment variables
$env:NODE_VERSION = $config.development.tools.node_version
$env:NPM_VERSION = $config.development.tools.npm_version

# Functions
function Test-Prerequisites {
    Write-Host "Checking prerequisites..."
    
    # Check Node.js
    $nodeVersion = node --version
    if (-not $?) {
        throw "Node.js is not installed"
    }
    
    # Check npm
    $npmVersion = npm --version
    if (-not $?) {
        throw "npm is not installed"
    }
    
    # Check gulp
    $gulpVersion = gulp --version
    if (-not $?) {
        Write-Host "Installing gulp..."
        npm install -g gulp-cli
    }
    
    # Check Yeoman
    $yoVersion = yo --version
    if (-not $?) {
        Write-Host "Installing Yeoman..."
        npm install -g yo
    }
}

function Install-Dependencies {
    Write-Host "Installing dependencies..."
    Push-Location $SolutionPath
    
    try {
        npm install
        if (-not $?) {
            throw "Failed to install dependencies"
        }
    }
    finally {
        Pop-Location
    }
}

function Build-Solution {
    if ($SkipBuild) {
        Write-Host "Skipping build..."
        return
    }
    
    Write-Host "Building solution..."
    Push-Location $SolutionPath
    
    try {
        # Clean previous build
        gulp clean
        
        # Build solution
        gulp build
        if (-not $?) {
            throw "Build failed"
        }
        
        # Bundle solution
        gulp bundle --ship
        if (-not $?) {
            throw "Bundle failed"
        }
        
        # Package solution
        gulp package-solution --ship
        if (-not $?) {
            throw "Package failed"
        }
    }
    finally {
        Pop-Location
    }
}

function Test-Solution {
    if ($SkipTest) {
        Write-Host "Skipping tests..."
        return
    }
    
    Write-Host "Running tests..."
    Push-Location $SolutionPath
    
    try {
        npm test
        if (-not $?) {
            throw "Tests failed"
        }
    }
    finally {
        Pop-Location
    }
}

function Deploy-Solution {
    Write-Host "Deploying solution to $Environment..."
    Push-Location $SolutionPath
    
    try {
        # Get environment URL
        $siteUrl = $config.sharepoint.development.environments.$Environment.site_url
        
        # Connect to SharePoint
        Connect-PnPOnline -Url $siteUrl -Interactive
        
        # Deploy package
        $packagePath = Join-Path $SolutionPath "sharepoint\solution\solution.sppkg"
        Add-PnPApp -Path $packagePath -Scope Site -Publish -Overwrite:$Force
        
        # Install app
        $app = Get-PnPApp | Where-Object { $_.Title -eq (Get-Item $SolutionPath).Name }
        Install-PnPApp -Identity $app.Id -Scope Site
        
        Write-Host "Deployment completed successfully"
    }
    catch {
        Write-Error "Deployment failed: $_"
        throw
    }
    finally {
        Pop-Location
    }
}

# Main execution
try {
    Test-Prerequisites
    Install-Dependencies
    Build-Solution
    Test-Solution
    Deploy-Solution
}
catch {
    Write-Error "Deployment failed: $_"
    exit 1
}
