# Beta.61 normalized notice-bearing package proposal

Status: **PROPOSED, NOT SELECTED, RELEASE BLOCKED**.

This local review connects the existing three private notice-bearing
prototypes and normalized Setup to the original application acceptance
subject. The outer package identities are distinct from the original
portable EXE and Apple inner archive identities. No application, signature
or notice bytes are changed. The proposed names and channels below are
not authorized release destinations.

| Proposed asset | Channel | SHA-256 | Local status |
| --- | --- | --- | --- |
| AJAZZBatteryTray-win-x64-notices.zip | beta | f22c7ed470ac798393ec94b5d61245bb17afea8d78eca3c0d866f3033977cfb3 | MATCH |
| AJAZZBatteryTray-Setup-win-x64.exe | beta | e7195b3817e919eeff47606c036089a2e9fabc44b2238eae466918b992da90a8 | NOT_PROVIDED |
| AJAZZBatteryTray-macOS-universal-notices.zip | beta | a3c837a0d673de8eccac182cf224503e54cf7b64d0bbcf6adb51dce755c025d8 | MATCH |
| AJAZZBatteryTray-macOS-HighSierra-Intel-notices.zip | high-sierra | 7b514bd2a2af310f0803822f8f8bbd80043c0cfca0af38fbb45b1a25f7b39db4 | MATCH |

Source: f939fea7fb422aa588649138d29a750ce62cd22a.
Original application/Setup acceptance subject:
913bda7686afff10036e681471169542175aef67345ab3c8cbb4fbb843144da6.
Proposed package subject:
f5cc915217a7100fecbb72813c1fedcc871e6d4c231763d90194f31e64b90800.

## Local verification

Use the exact original CI archives and original normalized evidence ZIP
from the hardware field kit, the three previously reviewed local prototypes
and the exact project MIT LICENSE. The prototype generation commands are in
[CANDIDATE_DISTRIBUTION_REVIEW.md](CANDIDATE_DISTRIBUTION_REVIEW.md).

```sh
python tools/review_normalized_package_set.py --normalized-evidence normalized-evidence.zip --windows-package private-portable-notices.zip --universal-package universal-notices-first.zip --high-sierra-package high-sierra-notices-first.zip --windows-archive windows.zip --universal-archive universal.zip --high-sierra-archive high-sierra.zip --license LICENSE --output package-proposal.json
```

Supply --setup PATH for the actual retained normalized Setup after obtaining
it in an authorized private environment. The command verifies all three
prototype identities and contents, exact original archive hashes and hosted
normalized evidence. It requires the exact Setup hash if supplied.
Exit 1 means the three packages match but Setup was not provided; exit 0
means all four local identities match; exit 2 means invalid inputs or
output failure. No exit code authorizes distribution or publication.
The output is written exclusively and does not replace prior evidence.

## Remaining decisions

- Obtain and retain the exact normalized Setup on an authorized private
  Windows system; its bytes are not retained by the reviewed hosted jobs.
- Execute the actual hardware and interactive cases on the exact application
  and Setup. Review final package extraction/launch behavior separately.
- Decide whether these proposed names and wrapper formats are appropriate
  for users, including existing update/client compatibility.
- Resolve outstanding distribution terms, asset provenance, notice scope,
  signing disposition and explicit publication approval for the exact set.

The actual local replay verified all three existing package files and
returned exit 1 with Setup NOT_PROVIDED. No package has been selected,
uploaded or released by this step.
