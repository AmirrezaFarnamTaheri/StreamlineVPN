param(
  [ValidateSet('dev-up','dev-down','prod-up','prod-down','validate')]
  [string]$Task = 'validate'
)

function Invoke-DevUp {
  docker compose -f docker-compose.dev.yml up -d --build
}
function Invoke-DevDown {
  docker compose -f docker-compose.dev.yml down -v
}
function Invoke-ProdUp {
  docker compose -f docker-compose.production.yml up -d --build
}
function Invoke-ProdDown {
  docker compose -f docker-compose.production.yml down -v
}
function Invoke-Validate {
  python scripts/comprehensive_validator.py
}

switch ($Task) {
  'dev-up'   { Invoke-DevUp }
  'dev-down' { Invoke-DevDown }
  'prod-up'  { Invoke-ProdUp }
  'prod-down'{ Invoke-ProdDown }
  'validate' { Invoke-Validate }
}

