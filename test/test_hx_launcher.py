from hendrix.options import HendrixOptionParser
from hendrix.ux import main


def test_no_arguments_gives_help_text(mocker):
    class MockFile(object):
        @classmethod
        def write(cls, whatever):
            cls.things_written = whatever

    class MockStdOut(object):

        @classmethod
        def write(cls, whatever):
            HendrixOptionParser.print_help(MockFile)
            assert MockFile.things_written == whatever

    mocker.patch('sys.stdout', new=MockStdOut)
    main([])
