import os
import shutil


def read_file(file_path):
    """
    INPUT:
    file_path: str, the path of the file to be read
    OUTPUT:
    values: 2d list of str, store the values of the records
    """
    with open(file_path, "r") as file:
        values = [line.strip().split() for line in file]

    return values


def read_and_sort_file(file_path, id_list=None, **kwargs):
    """
    INPUT:
    file_path: str, the path of the file to be read
    id_list: None or list of int, the ids of the records to be read
    OUTPUT:
    values: 2d list of str, store the sorted values of the (selected) records
    """
    values = read_file(file_path)

    if id_list is not None:
        values = [row for row in values if row[0] in id_list]

    values.sort(key=lambda row: row[0])

    return values


def delete_columns(two_d_list, col_del):
    """
    Delete the columns in col_del of two_d_list
    """
    for n in range(len(col_del)):
        for row in two_d_list:
            del row[col_del[n] - n - 1]


class TestClass:
    path = os.path.join("tests", "functional_tests")
    command = "AlphaPeel "
    test_cases = None
    input_file_depend_on_test_cases = None
    full_input = ["genotypes", "pedigree", "penetrance", "phasefile", "seqfile"]

    def mk_output_dir(self):
        """
        Prepare a empty folder at the input path
        """
        if os.path.exists(self.output_path):
            shutil.rmtree(self.output_path)

        os.mkdir(self.output_path)

    def generate_command(self):
        """
        generate the command for the test
        """
        for file in self.input_files:
            if (
                (self.test_cases is not None)
                and (self.input_file_depend_on_test_cases is not None)
                and (file in self.input_file_depend_on_test_cases)
            ):
                self.command += f"-{file} {os.path.join(self.path, f'{file}-{self.test_cases}.txt')} "
            else:
                self.command += f"-{file} {os.path.join(self.path, f'{file}.txt')} "

        for key, value in self.arguments.items():
            if value is not None:
                self.command += f"-{key} {value} "
            else:
                self.command += f"-{key} "

        self.command += (
            f"-out {os.path.join(self.output_path, self.output_file_prefix)}"
        )

    def prepare_path(self):
        """
        Initialize the paths for the test
        """
        self.path = os.path.join(self.path, self.test_name)
        self.output_path = os.path.join(self.path, "outputs")
        self.mk_output_dir()

    def check_files(self):
        """
        Check the existence of the output files
        """

        def check(file_type):
            return os.path.exists(
                os.path.join(self.output_path, f"{self.output_file_prefix}.{file_type}")
            )

        files = ["dosages", "seg", "maf", "genoError", "seqError", "haps"]
        return [check(file) for file in files]

    def test_files(self):
        """
        Can we read in unrelated individuals from multiple file formats and
        output the values to a normal dosage file
        """
        self.test_name = "test_files"
        self.prepare_path()

        self.input_files = self.full_input
        self.arguments = {
            "runType": "multi",
            "calling_threshold": ".1",
            "esterrors": None,
        }
        self.output_file_prefix = "files"
        self.output_file_to_check = "called.0.1"

        self.generate_command()
        os.system(self.command)

        self.output_file_path = os.path.join(
            self.output_path, f"{self.output_file_prefix}.{self.output_file_to_check}"
        )
        self.expected_file_path = os.path.join(self.path, "trueGenotypes.txt")

        self.output = read_and_sort_file(self.output_file_path)
        self.expected = read_and_sort_file(self.expected_file_path)

        assert self.output == self.expected

    def test_subset(self):
        """
        Can we read in a subset of values as in Test 1 output them and
        make sure it's the same chunk? (=testing startsnp and stopsnp)
        """
        self.test_name = "test_subset"
        self.prepare_path()

        self.input_files = self.full_input
        self.arguments = {
            "runType": "multi",
            "calling_threshold": ".1",
            "startsnp": "2",
            "stopsnp": "4",
        }
        self.output_file_prefix = "subset"
        self.output_file_to_check = "called.0.1"

        self.generate_command()
        os.system(self.command)

        self.output_file_path = os.path.join(
            self.output_path, f"{self.output_file_prefix}.{self.output_file_to_check}"
        )
        self.expected_file_path = os.path.join(self.path, "trueGenotypes.txt")

        self.output = read_and_sort_file(self.output_file_path)
        self.expected = read_and_sort_file(self.expected_file_path)

        delete_columns(self.expected, [2, 6])

        assert self.output == self.expected

    def test_writekey(self):
        """
        Can we read in values and return them in the correct order.
        Check id, pedigree, genotypes, sequence, segregation. Also check onlykeyed.
        """
        self.test_name = "test_writekey"
        self.prepare_path()

        self.input_files = self.full_input
        self.arguments = {
            "runType": "multi",
            "calling_threshold": ".1",
            "writekey": None,
        }

        methods = ["id", "pedigree", "genotypes", "sequence"]
        answer = {
            "id": "genotypes",
            "pedigree": "penetrance",
            "genotypes": "genotypes",
            "sequence": "seq",
        }

        self.output_file_to_check = "called.0.1"

        for self.test_cases in methods:
            self.arguments["writekey"] = self.test_cases
            self.output_file_prefix = f"writekey.{self.test_cases}"

            self.generate_command()
            os.system(self.command)

            self.output_file_path = os.path.join(
                self.output_path,
                f"{self.output_file_prefix}.{self.output_file_to_check}",
            )

            self.output = read_file(self.output_file_path)

            assert len(self.output) == 4
            assert self.output[0][0] == answer[self.test_cases]

            self.command = "AlphaPeel "

        self.test_cases = "onlykeyed"
        self.arguments["onlykeyed"] = None
        self.output_file_prefix = f"writekey.{self.test_cases}"

        self.generate_command()
        print(self.command)
        os.system(self.command)

        self.output_file_path = os.path.join(
            self.output_path, f"{self.output_file_prefix}.{self.output_file_to_check}"
        )

        self.output = read_file(self.output_file_path)

        assert len(self.output) == 1
        assert self.output[0][0] == "seq"

    def test_est(self):
        """
        Check -esterrors, -estmaf, -length just to make sure it runs.
        """
        self.test_name = "test_est"
        self.prepare_path()

        self.input_files = self.full_input
        self.input_file_depend_on_test_cases = self.full_input
        self.arguments = {"runType": "multi", "calling_threshold": ".1"}
        self.output_file_to_check = "called.0.1"

        for self.test_cases in ["esterror", "estmaf", "length"]:
            # TODO estrecombrate instead of just adding length
            if self.test_cases != "length":
                self.arguments[self.test_cases] = None
            else:
                # Do we need to continue use this value for lengh
                # as it is the same as the default value
                self.arguments["length"] = "1.0"
            self.output_file_prefix = f"est.{self.test_cases}"

            self.generate_command()
            os.system(self.command)

            self.output_file_path = os.path.join(
                self.output_path,
                f"{self.output_file_prefix}.{self.output_file_to_check}",
            )
            self.expected_file_path = os.path.join(
                self.path, f"trueGenotypes-{self.test_cases}.txt"
            )

            self.output = read_and_sort_file(self.output_file_path)
            self.expected = read_and_sort_file(self.expected_file_path)

            assert self.output == self.expected

            self.arguments.pop(self.test_cases)
            self.command = "AlphaPeel "

    def test_no(self):
        """
        Check to make sure the no_dosages, no_seg, no_params
        flags work, and the haps file works.
        """
        self.test_name = "test_no"
        self.prepare_path()

        self.input_files = self.full_input
        self.arguments = {"runType": "multi"}
        # whether the output files exist
        # 0: not exist
        # 1: exist
        expect = {
            "no_dosages": [0, 1, 1, 1, 1, 0],
            "no_seg": [1, 0, 1, 1, 1, 0],
            "no_params": [1, 1, 0, 0, 0, 0],
            "haps": [1, 1, 1, 1, 1, 1],
        }

        for self.test_cases in ["no_dosages", "no_seg", "no_params", "haps"]:
            self.arguments[self.test_cases] = None
            self.output_file_prefix = f"no.{self.test_cases}"

            self.generate_command()
            os.system(self.command)

            assert self.check_files() == expect[self.test_cases]

            self.arguments.pop(self.test_cases)
            self.command = "AlphaPeel "

    def test_rec(self):
        """
        Run the test of the recombination functionality of AlphaPeel
        """
        self.test_name = "test_rec"
        self.prepare_path()

        self.input_files = ["genotypes", "seqfile", "pedigree"]
        self.arguments = {"runType": "multi"}
        self.output_file_prefix = "rec"
        self.output_file_to_check = "seg"

        self.generate_command()
        os.system(self.command)

        self.output_file_path = os.path.join(
            self.output_path, f"{self.output_file_prefix}.{self.output_file_to_check}"
        )
        self.expected_file_path = os.path.join(self.path, "trueSeg.txt")

        self.output = read_and_sort_file(self.output_file_path)
        self.expected = read_and_sort_file(self.expected_file_path)

        assert self.output == self.expected

    # the true values to check against are wrong for test_sex
    # needs to rewrite
    def test_sex(self):
        """
        Run the test of the sex chromosome functionality of AlphaPeel
        -sexchrom still under development...
        """
        self.test_name = "test_sex"
        self.prepare_path()

        self.arguments = {"runType": "multi", "sexchrom": None}
        self.input_files = ["genotypes", "seqfile", "pedigree"]
        self.input_file_depend_on_test_cases = ["genotypes", "seqfile"]

        for self.test_cases in ["a", "b", "c", "d"]:
            # test case a: homozygous generation 2
            #           b: heterozygous generation 2
            #           c: with recombination in M2
            #           d: missing values in generation 2

            self.output_file_prefix = f"sex.{self.test_cases}"
            self.output_file_to_check = "seg"

            self.generate_command()
            print(self.command)
            os.system(self.command)

            self.output_file_path = os.path.join(
                self.output_path,
                f"{self.output_file_prefix}.{self.output_file_to_check}",
            )
            self.expected_file_path = os.path.join(
                self.path, f"trueSeg-{self.test_cases}.txt"
            )

            self.output = read_and_sort_file(self.output_file_path)
            self.expected = read_and_sort_file(self.expected_file_path)

            assert self.output == self.expected
            self.command = "AlphaPeel "

    # the true values to check against for test_error is not written yet
    def test_error(self):
        """
        Run the test of the correcting errors functionality of AlphaPeel
        """
        self.test_name = "test_error"
        self.prepare_path()

        # using default error rates: genotype error rate: 0.01
        #                            sequence error rate: 0.001
        self.arguments = {"runType": "multi"}
        self.input_files = ["genotypes", "seqfile", "pedigree"]
        self.input_file_depend_on_test_cases = ["genotypes", "seqfile"]

        for self.test_cases in ["a", "b", "c", "d"]:
            # test case a: somatic mutation at locus 5 of M1 in genotype and seqfile
            #           b: germline mutation at locus 5 of M1 in genotype and seqfile
            #           c: somatic mutation at locus 5 of M1 in seqfile only,
            #              with genotype value missing
            #           d: germline mutation at locus 5 of M1 in seqfile only,
            #              with genotype value missing

            self.output_file_prefix = f"error.{self.test_cases}"
            self.output_file_to_check = "genotypes"

            self.generate_command()
            print(self.command)
            os.system(self.command)

            #     self.output_file_path = os.path.join(
            #         self.output_path,
            #         f"{self.output_file_prefix}.{self.output_file_to_check}"
            #         )
            #     self.expected_file_path = os.path.join(self.path, f"trueSeg-{self.test_cases}.txt")

            #     self.output = read_and_sort_file(self.output_file_path)
            #     self.expected = read_and_sort_file(self.expected_file_path)

            #     assert self.output == self.expected
            self.command = "AlphaPeel "

    # TODO test_plink for PLINK
    #      a. binary PLINK output
    #      b. binary output + input
    #      c. pedigree

    # TODO test_onlykeyed for onlykeyed with halffounders
