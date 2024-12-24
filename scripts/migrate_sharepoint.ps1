# SharePoint Migration Script
param(
    [Parameter(Mandatory=$true)]
    [string]$SourceUrl,
    
    [Parameter(Mandatory=$true)]
    [string]$TargetUrl,
    
    [Parameter(Mandatory=$true)]
    [string]$MigrationTool,
    
    [Parameter(Mandatory=$false)]
    [switch]$SkipAssessment,
    
    [Parameter(Mandatory=$false)]
    [switch]$Force
)

# Import configuration
$configPath = Join-Path $PSScriptRoot "..\config\templates\sharepoint_dev_config_template.json"
$config = Get-Content $configPath | ConvertFrom-Json

# Functions
function Test-Prerequisites {
    Write-Host "Checking prerequisites..."
    
    switch ($MigrationTool) {
        "ShareGate" {
            $sharegate = Get-Command "ShareGate.exe" -ErrorAction SilentlyContinue
            if (-not $sharegate) {
                throw "ShareGate is not installed"
            }
        }
        "Metalogix" {
            $metalogix = Get-Command "MetalogixOnline.exe" -ErrorAction SilentlyContinue
            if (-not $metalogix) {
                throw "Metalogix is not installed"
            }
        }
        default {
            throw "Unsupported migration tool: $MigrationTool"
        }
    }
}

function Invoke-PreMigrationAssessment {
    if ($SkipAssessment) {
        Write-Host "Skipping pre-migration assessment..."
        return
    }
    
    Write-Host "Running pre-migration assessment..."
    
    # Connect to source
    Connect-PnPOnline -Url $SourceUrl -Interactive
    
    # Assess content
    $assessment = @{
        ContentTypes = Get-PnPContentType
        Lists = Get-PnPList
        Workflows = Get-PnPWorkflowDefinition
        CustomSolutions = Get-PnPSolution
        Features = Get-PnPFeature
    }
    
    # Generate report
    $reportPath = ".\migration_assessment_$(Get-Date -Format 'yyyyMMdd_HHmmss').json"
    $assessment | ConvertTo-Json -Depth 10 | Out-File $reportPath
    
    Write-Host "Assessment report saved to: $reportPath"
    
    # Check for potential issues
    $issues = @()
    
    # Check workflows
    if ($assessment.Workflows.Count -gt 0) {
        $issues += "Found $(assessment.Workflows.Count) workflows that need to be recreated in Power Automate"
    }
    
    # Check custom solutions
    if ($assessment.CustomSolutions.Count -gt 0) {
        $issues += "Found $(assessment.CustomSolutions.Count) custom solutions that need to be migrated"
    }
    
    if ($issues.Count -gt 0) {
        Write-Warning "Found potential migration issues:"
        $issues | ForEach-Object { Write-Warning "- $_" }
        
        if (-not $Force) {
            $continue = Read-Host "Do you want to continue? (Y/N)"
            if ($continue -ne "Y") {
                throw "Migration cancelled by user"
            }
        }
    }
}

function Invoke-ShareGateMigration {
    Write-Host "Starting ShareGate migration..."
    
    # Load ShareGate PowerShell module
    Import-Module ShareGatePS
    
    # Connect to source and destination
    $sourceConnection = Connect-Site -Url $SourceUrl
    $destConnection = Connect-Site -Url $TargetUrl
    
    # Set migration settings
    $copySettings = New-CopySettings -OnContentItemExists IncrementalUpdate `
                                   -OnSiteObjectExists IncrementalUpdate `
                                   -IncludePermissions:$config.migration.tools.sharegate.settings.copy_permissions `
                                   -IncludeVersions:$true
    
    # Start migration
    $migration = Copy-Site -Source $sourceConnection `
                          -Destination $destConnection `
                          -CopySettings $copySettings
    
    # Generate report
    $reportPath = ".\migration_report_$(Get-Date -Format 'yyyyMMdd_HHmmss').xlsx"
    Export-Report -Migration $migration -Path $reportPath
    
    Write-Host "Migration completed. Report saved to: $reportPath"
}

function Invoke-MetalogixMigration {
    Write-Host "Starting Metalogix migration..."
    
    # Load Metalogix PowerShell module
    Import-Module MetalogixOnline
    
    # Connect to source and destination
    Connect-MetalogixOnline -Url $SourceUrl
    Connect-MetalogixOnline -Url $TargetUrl
    
    # Set migration settings
    $migrationSettings = @{
        PreserveVersions = $config.migration.tools.metalogix.settings.preserve_versions
        PreservePermissions = $config.migration.tools.metalogix.settings.preserve_permissions
        MigrateWorkflows = $config.migration.tools.metalogix.settings.migrate_workflows
    }
    
    # Start migration
    $job = Start-MetalogixMigration -Source $SourceUrl `
                                   -Destination $TargetUrl `
                                   -Settings $migrationSettings
    
    # Wait for completion
    Wait-MetalogixMigration -Job $job
    
    # Generate report
    $reportPath = ".\migration_report_$(Get-Date -Format 'yyyyMMdd_HHmmss').xlsx"
    Export-MetalogixReport -Job $job -Path $reportPath
    
    Write-Host "Migration completed. Report saved to: $reportPath"
}

function Test-MigrationResults {
    Write-Host "Validating migration results..."
    
    # Connect to source and destination
    Connect-PnPOnline -Url $SourceUrl -Interactive
    $sourceLists = Get-PnPList
    
    Connect-PnPOnline -Url $TargetUrl -Interactive
    $targetLists = Get-PnPList
    
    # Compare content
    $validation = @{
        Lists = Compare-Object -ReferenceObject $sourceLists -DifferenceObject $targetLists -Property Title
        ContentTypes = Compare-Object -ReferenceObject (Get-PnPContentType) -DifferenceObject (Get-PnPContentType) -Property Name
        ItemCounts = @{}
    }
    
    # Compare item counts
    foreach ($list in $sourceLists) {
        $sourceCount = (Get-PnPListItem -List $list.Title).Count
        $targetCount = (Get-PnPListItem -List $list.Title).Count
        
        $validation.ItemCounts[$list.Title] = @{
            Source = $sourceCount
            Target = $targetCount
            Difference = $sourceCount - $targetCount
        }
    }
    
    # Generate validation report
    $reportPath = ".\migration_validation_$(Get-Date -Format 'yyyyMMdd_HHmmss').json"
    $validation | ConvertTo-Json -Depth 10 | Out-File $reportPath
    
    Write-Host "Validation report saved to: $reportPath"
    
    # Check for discrepancies
    $issues = @()
    
    if ($validation.Lists) {
        $issues += "Found differences in list structure"
    }
    
    if ($validation.ContentTypes) {
        $issues += "Found differences in content types"
    }
    
    $itemDiscrepancies = $validation.ItemCounts.Values | Where-Object { $_.Difference -ne 0 }
    if ($itemDiscrepancies) {
        $issues += "Found differences in item counts for $($itemDiscrepancies.Count) lists"
    }
    
    if ($issues) {
        Write-Warning "Validation found issues:"
        $issues | ForEach-Object { Write-Warning "- $_" }
    }
    else {
        Write-Host "Validation completed successfully"
    }
}

# Main execution
try {
    Test-Prerequisites
    Invoke-PreMigrationAssessment
    
    switch ($MigrationTool) {
        "ShareGate" { Invoke-ShareGateMigration }
        "Metalogix" { Invoke-MetalogixMigration }
    }
    
    Test-MigrationResults
}
catch {
    Write-Error "Migration failed: $_"
    exit 1
}
