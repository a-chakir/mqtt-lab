# Part III - Contract Net Protocol

## Description
Implementation of the Contract Net coordination protocol for job scheduling across multiple machines.

## Protocol Flow
```
1. Supervisor sends CfP (Call for Proposal) to all machines
2. Machines respond with:
   - Proposal (bid) if they can do the job
   - Rejection if busy or incapable
3. Supervisor waits for deadline
4. Supervisor evaluates bids, selects winner (lowest time)
5. Winner receives Award, starts job execution
6. Other bidders receive Rejection
7. Machine is busy until job completes
```

## Topic Structure
```
cfp/jobs              - Call for proposals (broadcast)
bids/<job_id>         - Machines submit bids/rejections
awards/<machine_id>   - Job awards to specific machines
rejects/<machine_id>  - Bid rejections
```

## Design Choices

### Machine ID Retrieval
Machine IDs are included in bid messages (`machine_id` field), making it easy for the supervisor to identify bidders without parsing topics.

### Job Dispatching
Awards are sent to specific machine topics (`awards/<machine_id>`), ensuring only the winner receives the assignment. Rejections are also sent individually.

### Single CfP Topic
All CfPs are broadcast on `cfp/jobs`. Each machine filters based on its capabilities.

## Quick Start
```bash
# Run complete simulation (4 machines, 10 jobs)
python run_simulation.py

# Custom configuration
python run_simulation.py --machines 5 --jobs 20
```

## Manual Mode

### Terminal 1-4: Machines
```bash
python machine.py --id machine_A --capabilities assembly:4 inspection:2
python machine.py --id machine_B --capabilities welding:5 painting:4
python machine.py --id machine_C --capabilities assembly:6 packaging:3
python machine.py --id machine_D --capabilities welding:8 inspection:3
```

### Terminal 5: Supervisor
```bash
python supervisor.py --jobs 10 --deadline 5
```

## Parameters

### supervisor.py
| Parameter | Default | Description |
|-----------|---------|-------------|
| `--jobs` | 10 | Number of jobs to dispatch |
| `--deadline` | 5 | Seconds to wait for bids |
| `--interval` | 3 | Seconds between jobs |

### machine.py
| Parameter | Default | Description |
|-----------|---------|-------------|
| `--id` | required | Unique machine ID |
| `--capabilities` | assembly:5 inspection:3 | Job:time pairs |

## Job Types
- `assembly` - Assemble components
- `welding` - Weld parts together
- `painting` - Paint surfaces
- `inspection` - Quality inspection
- `packaging` - Package for shipping
